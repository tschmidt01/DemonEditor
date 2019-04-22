from app.commons import run_idle
from app.eparser.ecommons import BouquetService, BqServiceType
from app.tools.epg import EPG, ChannelsParser
from app.ui.dialogs import get_message
from .main_helper import on_popup_menu
from .uicommons import Gtk, Gdk, UI_RESOURCES_PATH, TEXT_DOMAIN, Column, EPG_ICON


class EpgDialog:

    def __init__(self, transient, options, services, bouquet, fav_model):

        handlers = {"on_apply": self.on_apply,
                    "on_save_to_xml": self.on_save_to_xml,
                    "on_options": self.on_options,
                    "on_auto_configuration": self.on_auto_configuration,
                    "on_filter_toggled": self.on_filter_toggled,
                    "on_filter_changed": self.on_filter_changed,
                    "on_info_bar_close": self.on_info_bar_close,
                    "on_popup_menu": on_popup_menu,
                    "on_drag_begin": self.on_drag_begin,
                    "on_drag_data_get": self.on_drag_data_get,
                    "on_drag_data_received": self.on_drag_data_received,
                    "on_resize": self.on_resize}

        self._services = services
        self._ex_fav_model = fav_model
        self._options = options
        self._bouquet = bouquet

        builder = Gtk.Builder()
        builder.set_translation_domain(TEXT_DOMAIN)
        builder.add_from_file(UI_RESOURCES_PATH + "epg_dialog.glade")
        builder.connect_signals(handlers)

        self._dialog = builder.get_object("epg_dialog_window")
        self._dialog.set_transient_for(transient)
        self._source_view = builder.get_object("source_view")
        self._bouquet_view = builder.get_object("bouquet_view")
        self._bouquet_model = builder.get_object("bouquet_list_store")
        self._services_model = builder.get_object("services_list_store")
        self._info_bar = builder.get_object("info_bar")
        self._message_label = builder.get_object("info_bar_message_label")
        # Filter
        self._filter_bar = builder.get_object("filter_bar")
        self._filter_entry = builder.get_object("filter_entry")
        self._services_filter_model = builder.get_object("services_filter_model")
        self._services_filter_model.set_visible_func(self.services_filter_function)
        # Setting the last size of the dialog window
        window_size = self._options.get("epg_tool_window_size", None)
        if window_size:
            self._dialog.resize(*window_size)

        self.init_drag_and_drop()
        self.init_data()

    @run_idle
    def init_data(self):
        for r in self._ex_fav_model:
            row = [*r[:]]
            self._bouquet_model.append(row)

        try:
            refs = EPG.get_epg_refs(self._options.get("data_dir_path", "") + "epg.dat")
            # for source lamedb
            srvs = {k[:k.rfind(":")]: v for k, v in self._services.items()}
            list(map(self._services_model.append,
                     map(lambda s: (s.service, s.fav_id),
                         filter(None, [srvs.get(ref) for ref in refs]))))
        except (FileNotFoundError, ValueError) as e:
            self.show_info_message("Read epg.dat error: {}".format(e), Gtk.MessageType.ERROR)
        else:
            if len(self._services_model) == 0:
                msg = "Current epg.dat file does not contains references for the services of this bouquet!"
                self.show_info_message(msg, Gtk.MessageType.ERROR)

    def show(self):
        self._dialog.show()

    @run_idle
    def on_apply(self, item):
        self._bouquet.clear()
        list(map(self._bouquet.append, [r[Column.FAV_ID] for r in self._bouquet_model]))
        for index, row in enumerate(self._ex_fav_model):
            row[Column.FAV_ID] = self._bouquet[index]

        self.show_info_message(get_message("Done!"), Gtk.MessageType.INFO)

    @run_idle
    def on_save_to_xml(self, item):
        services = []
        iptv_types = (BqServiceType.IPTV.value, BqServiceType.MARKER.value)
        for r in self._bouquet_model:
            srv_type = r[Column.FAV_TYPE]
            if srv_type in iptv_types:
                srv = BouquetService(name=r[Column.FAV_SERVICE],
                                     type=BqServiceType(srv_type),
                                     data=r[Column.FAV_ID],
                                     num=r[Column.FAV_NUM])
                services.append(srv)

        ChannelsParser.write_refs_to_xml(self._options.get("data_dir_path", "") + "channels.xml", services)
        self.show_info_message(get_message("Done!"), Gtk.MessageType.INFO)

    def on_options(self, item):
        pass

    def on_auto_configuration(self, item):
        source = {"".join(r[0].split()).upper(): r[1] for r in self._services_model}
        success_count = 0

        for r in self._bouquet_model:
            name = "".join(r[Column.FAV_SERVICE].split()).upper()
            ref = source.get(name, None)
            if ref:
                self.assign_data(r, ref)
                success_count += 1

        self.show_info_message("Done! Count of successfully configured services: {}".format(success_count),
                               Gtk.MessageType.INFO)

    def assign_data(self, row, ref):
        row[Column.FAV_LOCKED] = EPG_ICON
        fav_id = row[Column.FAV_ID]
        fav_id_data = fav_id.split(":")
        fav_id_data[3:7] = ref.split(":")
        new_fav_id = ":".join(fav_id_data)
        service = self._services.pop(fav_id)
        self._services[new_fav_id] = service._replace(fav_id=new_fav_id)
        row[Column.FAV_ID] = new_fav_id

    def on_filter_toggled(self, button: Gtk.ToggleButton):
        self._filter_bar.set_search_mode(button.get_active())

    def on_filter_changed(self, entry):
        self._services_filter_model.refilter()

    def services_filter_function(self, model, itr, data):
        txt = self._filter_entry.get_text().upper()
        return model is None or model == "None" or txt in model.get_value(itr, 0).upper()

    def on_info_bar_close(self, bar=None, resp=None):
        self._info_bar.set_visible(False)

    @run_idle
    def show_info_message(self, text, message_type):
        self._info_bar.set_visible(True)
        self._info_bar.set_message_type(message_type)
        self._message_label.set_text(text)

    # ***************** Drag-and-drop *********************#
    def init_drag_and_drop(self):
        """ Enable drag-and-drop """
        target = []
        self._source_view.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, target, Gdk.DragAction.COPY)
        self._source_view.drag_source_add_text_targets()
        self._bouquet_view.enable_model_drag_dest(target, Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE)
        self._bouquet_view.drag_dest_add_text_targets()

    def on_drag_begin(self, view, context):
        """ Selects a row under the cursor in the view at the dragging beginning. """
        selection = view.get_selection()
        if selection.count_selected_rows() > 1:
            view.do_toggle_cursor_row(view)

    def on_drag_data_get(self, view: Gtk.TreeView, drag_context, data, info, time):
        model, paths = view.get_selection().get_selected_rows()
        if paths:
            val = model.get_value(model.get_iter(paths), 1)
            data.set_text(val, -1)

    def on_drag_data_received(self, view: Gtk.TreeView, drag_context, x, y, data, info, time):
        path, pos = view.get_dest_row_at_pos(x, y)
        model = view.get_model()
        self.assign_data(model[path], data.get_text())
        return False

    def on_resize(self, window):
        if self._options:
            self._options["epg_tool_window_size"] = window.get_size()


if __name__ == "__main__":
    pass