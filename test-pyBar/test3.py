#!/usr/bin/env python

# example treeviewdnd.py

from gi.repository import Gtk, Gdk, Pango, GObject

class TreeViewDnDExample:

    TARGETS = [
        ('MY_TREE_MODEL_ROW', Gtk.TargetFlags.SAME_WIDGET, 0),
        ('text/plain', 0, 1),
        ('TEXT', 0, 2),
        ('STRING', 0, 3),
        ]
    # close the window and quit
    def delete_event(self, widget, event, data=None):
        Gtk.main_quit()
        return False

    def clear_selected(self, button):
        selection = self.treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            model.remove(iter)
        return

    def __init__(self):
        # Create a new window
        self.window = Gtk.Window()

        self.window.set_title("URL Cache")

        self.window.set_size_request(200, 200)

        self.window.connect("delete_event", self.delete_event)

        self.scrolledwindow = Gtk.ScrolledWindow()
        self.vbox = Gtk.VBox()
        self.hbox = Gtk.HButtonBox()
        self.vbox.pack_start(self.scrolledwindow, True, True, 0)
        self.vbox.pack_start(self.hbox, False, True, 0)
        self.b0 = Gtk.Button('Clear All')
        self.b1 = Gtk.Button('Clear Selected')
        self.hbox.pack_start(self.b0, True, True, 0)
        self.hbox.pack_start(self.b1, True, True, 0)

        # create a liststore with one string column to use as the model
        self.liststore = Gtk.ListStore(str)

        # create the TreeView using liststore
        self.treeview = Gtk.TreeView(self.liststore)

       # create a CellRenderer to render the data
        self.cell = Gtk.CellRendererText()

        # create the TreeViewColumns to display the data
        self.tvcolumn = Gtk.TreeViewColumn('URL', self.cell, text=0)

        # add columns to treeview
        self.treeview.append_column(self.tvcolumn)
        self.b0.connect_object('clicked', Gtk.ListStore.clear, self.liststore)
        self.b1.connect('clicked', self.clear_selected)
        # make treeview searchable
        self.treeview.set_search_column(0)

        # Allow sorting on the column
        self.tvcolumn.set_sort_column_id(0)

        # Allow enable drag and drop of rows including row move
        self.treeview.enable_model_drag_source( Gdk.ModifierType.BUTTON1_MASK,
                                                self.TARGETS,
                                                Gdk.DragAction.DEFAULT|
                                                Gdk.DragAction.MOVE)
        self.treeview.enable_model_drag_dest(self.TARGETS,
                                             Gdk.DragAction.DEFAULT)
        self.treeview.drag_dest_add_text_targets()
        self.treeview.drag_source_add_text_targets()

        self.treeview.connect("drag_data_get", self.drag_data_get_data)
        self.treeview.connect("drag_data_received",
                              self.drag_data_received_data)

        self.scrolledwindow.add(self.treeview)
        self.window.add(self.vbox)
        self.window.show_all()

    def drag_data_get_data(self, treeview, context, selection, target_id,
                           etime):
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        data = bytes(model.get_value(iter, 0), "utf-8")
        selection.set(selection.get_target(), 8, data)

    def drag_data_received_data(self, treeview, context, x, y, selection,
                                info, etime):
        model = treeview.get_model()
        data = selection.get_data().decode("utf-8")
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            path, position = drop_info
            iter = model.get_iter(path)
            if (position == Gtk.TreeViewDropPosition.BEFORE
                or position == Gtk.TreeViewDropPosition.BEFORE):
                model.insert_before(iter, [data])
            else:
                model.insert_after(iter, [data])
        else:
            model.append([data])
        if context.get_actions() == Gdk.DragAction.MOVE:
            context.finish(True, True, etime)
        return

def main():
    Gtk.main()

if __name__ == "__main__":
    treeviewdndex = TreeViewDnDExample()
    main()
