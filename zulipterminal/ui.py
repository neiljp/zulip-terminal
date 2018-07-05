import platform
import re
from typing import Any, Tuple, List

import urwid

from zulipterminal.config import get_key
from zulipterminal.ui_tools.boxes import WriteBox, SearchBox
from zulipterminal.ui_tools.buttons import (
    HomeButton,
    PMButton,
    StreamButton,
)
from zulipterminal.ui_tools.views import (
    RightColumnView,
    MiddleColumnView,
    StreamsView,
)


class View(urwid.WidgetWrap):
    """
    A class responsible for providing the application's interface.
    """
    palette = {
        'default': [
                (None,           'light gray',    'black'),
                ('selected',     'light magenta', 'dark blue'),
                ('msg_selected', 'light red',     'black'),
                ('header',       'dark cyan',     'dark blue',  'bold'),
                ('custom',       'white',         'dark blue',  'underline'),
                ('content',      'white',         'black',      'standout'),
                ('name',         'yellow',        'black'),
                ('unread',       'black',         'light gray'),
                ('active',       'white',         'black'),
                ('idle',         'yellow',        'black')
                ],
        'light': [
                (None,           'black',        'white'),
                ('selected',     'white',        'dark blue'),
                ('msg_selected', 'dark blue',    'light gray'),
                ('header',       'white',        'dark blue',  'bold'),
                ('custom',       'white',        'dark blue',  'underline'),
                ('content',      'black',        'light gray', 'standout'),
                ('name',         'dark magenta', 'light gray', 'bold'),
                ],
        'blue': [
                (None,           'black',        'light blue'),
                ('selected',     'white',        'dark blue'),
                ('msg_selected', 'black',        'light gray'),
                ('header',       'black',        'dark blue',  'bold'),
                ('custom',       'white',        'dark blue',  'underline'),
                ('content',      'black',        'light gray', 'standout'),
                ('name',         'dark red',     'light gray', 'bold'),
                ]
                }

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.model = controller.model
        self.client = controller.client
        self.users = self.model.users
        self.pinned_streams = self.model.pinned_streams
        self.unpinned_streams = self.model.unpinned_streams
        self.write_box = WriteBox(self)
        self.search_box = SearchBox(self.controller)
        self.stream_w = []  # type: List[Any]
        super(View, self).__init__(self.main_window())

    def menu_view(self) -> Any:
        count = self.model.unread_counts.get('all_msg', 0)
        self.home_button = HomeButton(self.controller, count=count)
        count = self.model.unread_counts.get('all_pms', 0)
        self.pm_button = PMButton(self.controller, count=count)
        menu_btn_list = [
            self.home_button,
            urwid.Divider(),
            self.pm_button,
            ]
        w = urwid.ListBox(urwid.SimpleFocusListWalker(menu_btn_list))
        return w

    def streams_view(self, *, stream_list: List[List[Any]], title: str) -> Any:
        streams_btn_list = list()
        for stream in stream_list:
            unread_count = self.model.unread_counts.get(stream[1], 0)
            streams_btn_list.append(
                    StreamButton(
                        stream,
                        controller=self.controller,
                        view=self,
                        count=unread_count,
                    )
            )
        stream_view = StreamsView(streams_btn_list)
        self.stream_w.extend(stream_view.log)  # For multiple calls
        w = urwid.LineBox(stream_view, title=title)
        return w

    def left_column_view(self) -> Any:
        if not self.pinned_streams:
            pinned_weight = 0
            unpinned_title = "Streams"
        else:
            pinned_weight = 1
            unpinned_title = "Other Streams"

        if not self.unpinned_streams:
            unpinned_weight = 0
        else:
            unpinned_weight = 1

        pinned = self.streams_view(stream_list=self.pinned_streams,
                                   title="Pinned Streams")
        unpinned = self.streams_view(stream_list=self.unpinned_streams,
                                     title=unpinned_title)
        if pinned_weight == 0:
            pinned = urwid.WidgetDisable(pinned)
        if unpinned_weight == 0:
            unpinned = urwid.WidgetDisable(unpinned)

        left_column_structure = [
            (4, self.menu_view()),
            ('weight', pinned_weight, pinned),
            ('weight', unpinned_weight, unpinned),
        ]
        w = urwid.Pile(left_column_structure)
        return w

    def message_view(self) -> Any:
        self.middle_column = MiddleColumnView(self.model, self.write_box,
                                              self.search_box)
        w = urwid.LineBox(self.middle_column)
        return w

    def right_column_view(self) -> Any:
        self.users_view = RightColumnView(self)
        w = urwid.LineBox(self.users_view, title=u"Users")
        return w

    def main_window(self) -> Any:
        left_column = self.left_column_view()
        center_column = self.message_view()
        right_column = self.right_column_view()
        body = [
            ('weight', 3, left_column),
            ('weight', 10, center_column),
            ('weight', 3, right_column),
        ]
        self.body = urwid.Columns(body, focus_column=1)
        w = urwid.LineBox(self.body, title=u"Zulip")
        return w

    def keypress(self, size: Tuple[int, int], key: str) -> str:
        if self.controller.editor_mode:
            return self.controller.editor.keypress((size[1],), key)
        elif key == "w":
            # Start User Search if not in editor_mode
            self.users_view.keypress(size, 'w')
            self.body.focus_col = 2
            self.user_search.set_edit_text("")
            self.controller.editor_mode = True
            self.controller.editor = self.user_search
            return key

        else:
            return super(View, self).keypress(size, get_key(key))


class Screen(urwid.raw_display.Screen):

    def write(self, data: Any) -> None:
        if "Microsoft" in platform.platform():
            # replace urwid's SI/SO, which produce artifacts under WSL.
            # https://github.com/urwid/urwid/issues/264#issuecomment-358633735
            # Above link describes the change.
            data = re.sub("[\x0e\x0f]", "", data)
        super().write(data)
