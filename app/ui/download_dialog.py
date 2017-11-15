from app.commons import run_idle, run_task
from app.ftp import download_data, DownloadDataType, upload_data
from . import Gtk
from .dialogs import show_dialog


def show_download_dialog(transient, options, open_data):
    dialog = DownloadDialog(transient, options, open_data)
    dialog.run()
    dialog.destroy()


class DownloadDialog:
    def __init__(self, transient, properties, open_data):
        self._properties = properties
        self._open_data = open_data

        handlers = {"on_receive": self.on_receive,
                    "on_send": self.on_send,
                    "on_info_bar_close": self.on_info_bar_close}

        builder = Gtk.Builder()
        builder.add_objects_from_file("app/ui/dialogs.glade", ("download_dialog",))
        builder.connect_signals(handlers)

        self._dialog = builder.get_object("download_dialog")
        self._dialog.set_transient_for(transient)
        self._info_bar = builder.get_object("info_bar")
        self._message_label = builder.get_object("info_bar_message_label")
        self._host_entry = builder.get_object("host_entry").set_text(properties["host"])
        self._data_path_entry = builder.get_object("data_path_entry").set_text(properties["data_dir_path"])
        self._remove_unused_check_button = builder.get_object("remove_unused_check_button")
        self._all_radio_button = builder.get_object("all_radio_button")
        self._bouquets_radio_button = builder.get_object("bouquets_radio_button")
        self._satellites_radio_button = builder.get_object("satellites_radio_button")
        # self._dialog.get_content_area().set_border_width(0)

    @run_idle
    def on_receive(self, item):
        self.download(True, d_type=self.get_download_type())

    @run_idle
    def on_send(self, item):
        if show_dialog("question_dialog", self._dialog) != Gtk.ResponseType.CANCEL:
            self.download(d_type=self.get_download_type())

    def get_download_type(self):
        download_type = DownloadDataType.ALL
        if self._bouquets_radio_button.get_active():
            download_type = DownloadDataType.BOUQUETS
        elif self._satellites_radio_button.get_active():
            download_type = DownloadDataType.SATELLITES
        return download_type

    def run(self):
        return self._dialog.run()

    def destroy(self):
        self._dialog.destroy()

    def on_info_bar_close(self, *args):
        self._info_bar.set_visible(False)

    @run_idle
    @run_task
    def download(self, download=False, d_type=DownloadDataType.ALL):
        """ Download/upload data from/to receiver """
        try:
            if download:
                download_data(properties=self._properties, download_type=d_type)
            else:
                self.show_info_message("Please, wait...", Gtk.MessageType.INFO)
                upload_data(properties=self._properties,
                            download_type=d_type,
                            remove_unused=self._remove_unused_check_button.get_active())
        except Exception as e:
            self.show_info_message(getattr(e, "message", str(e)), Gtk.MessageType.ERROR)
        else:
            self.show_info_message("Done!", Gtk.MessageType.INFO)
            if download and d_type is not DownloadDataType.SATELLITES:
                self._open_data()

    @run_idle
    def show_info_message(self, text, message_type):
        self._info_bar.set_visible(True)
        self._info_bar.set_message_type(message_type)
        self._message_label.set_text(text)


if __name__ == "__main__":
    pass