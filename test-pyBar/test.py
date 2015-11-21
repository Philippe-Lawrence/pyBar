#!/usr/bin/python
# -*- coding: utf-8 -*-

from gi.repository import Gtk, Gdk

window = Gtk.Window()
window.set_size_request(300, 200)
window.connect('delete_event', lambda w,e: Gtk.main_quit())

# Define Liblarch Tree

store = Gtk.TreeStore(str, str)
store.insert(None, -1, ["A", "Task A"])
store.insert(None, -1, ["B", "Task B"])
store.insert(None, -1, ["C", "Task C"])
d_parent = store.insert(None, -1, ["D", "Task D"])
store.insert(d_parent, -1, ["E", "Task E"])

# Define TreeView in similar way as it happens in GTG/Liblarch_gtk
tv = Gtk.TreeView()

col = Gtk.TreeViewColumn()
col.set_title("Title")
render_text = Gtk.CellRendererText()
col.pack_start(render_text, expand=True)
col.add_attribute(render_text, 'markup', 1)
col.set_resizable(True)
col.set_expand(True)
col.set_sort_column_id(0)
tv.append_column(col)
tv.set_property("expander-column", col)

treemodel = store

def _sort_func(model, iter1, iter2):
    """ Sort two iterators by function which gets node objects.
    This is a simple wrapper which prepares node objects and then
    call comparing function. In other case return default value -1
    """
    node_a = model.get_value(iter1, 0)
    node_b = model.get_value(iter2, 0)
    if node_a and node_b:
        sort = cmp(node_a, node_b)
    else:
        sort = -1
    return sort

treemodel.set_sort_func(1, _sort_func)
tv.set_model(treemodel)

def on_child_toggled(treemodel2, path, iter, param=None):
    """ Expand row """
    if not tv.row_expanded(path):
        tv.expand_row(path, True)

treemodel.connect('row-has-child-toggled', on_child_toggled)

tv.set_search_column(1)
tv.set_property("enable-tree-lines", False)
tv.set_rules_hint(False)


#### Drag and drop stuff

dnd_internal_target = ''
dnd_external_targets = {}

def on_drag_fail(widget, dc, result):
    print ("Failed dragging", widget, dc, result)

def __init_dnd():
    """ Initialize Drag'n'Drop support

    Firstly build list of DND targets:
        * name
        * scope - just the same widget / same application
        * id

    Enable DND by calling enable_model_drag_dest(), 
    enable_model-drag_source()

    It didnt use support from Gtk.Widget(drag_source_set(),
    drag_dest_set()). To know difference, look in PyGTK FAQ:
    http://faq.pygtk.org/index.py?file=faq13.033.htp&req=show
    """
    #defer_select = False

    if dnd_internal_target == '':
        error = 'Cannot initialize DND without a valid name\n'
        error += 'Use set_dnd_name() first'
        raise Exception(error)

    dnd_targets = [(dnd_internal_target, Gtk.TargetFlags.SAME_WIDGET, 0)]
    for target in dnd_external_targets:
        name = dnd_external_targets[target][0]
        dnd_targets.append((name, Gtk.TARGET_SAME_APP, target))

    tv.enable_model_drag_source( Gdk.ModifierType.BUTTON1_MASK,
        dnd_targets, Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE)

    tv.enable_model_drag_dest(\
        dnd_targets, Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE)


def on_drag_data_get(treeview, context, selection, info, timestamp):
    """ Extract data from the source of the DnD operation.

    Serialize iterators of selected tasks in format 
    <iter>,<iter>,...,<iter> and set it as parameter of DND """
    print ("on_drag_data_get(", treeview, context, selection, info, timestamp)

    treeselection = treeview.get_selection()
    model, paths = treeselection.get_selected_rows()
    iters = [model.get_iter(path) for path in paths]
    iter_str = ','.join([model.get_string_from_iter(iter) for iter in iters])
    selection.set(dnd_internal_target, 0, iter_str)
    print ("Sending", iter_str)

def on_drag_data_received(treeview, context, x, y, selection, info,\
                          timestamp):
    """ Handle a drop situation.

    First of all, we need to get id of node which should accept
    all draged nodes as their new children. If there is no node,
    drop to root node.

    Deserialize iterators of dragged nodes (see self.on_drag_data_get())
    Info parameter determines which target was used:
        * info == 0 => internal DND within this TreeView
        * info > 0 => external DND

    In case of internal DND we just use Tree.move_node().
    In case of external DND we call function associated with that DND
    set by self.set_dnd_external()
    """
    print ("on_drag_data_received", treeview, context, x, y, selection, info, timestamp)

    model = treeview.get_model()
    destination_iter = None
    destination_tid = None
    drop_info = treeview.get_dest_row_at_pos(x, y)
    if drop_info:
        path, position = drop_info
        destination_iter = model.get_iter(path)
        if destination_iter:
            destination_tid = model.get_value(destination_iter, 0)

    # Get dragged iter as a TaskTreeModel iter
    # If there is no selected task (empty selection.data), 
    # explictly skip handling it (set to empty list)
    if selection.data == '':
        iters = []
    else:
        iters = selection.data.split(',')

    dragged_iters = []
    for iter in iters:
        print ("Info", info)
        if info == 0:
            try:
                dragged_iters.append(model.get_iter_from_string(iter))
            except ValueError:
                #I hate to silently fail but we have no choice.
                #It means that the iter is not good.
                #Thanks shitty Gtk API for not allowing us to test the string
                print ("Shitty iter", iter)
                dragged_iter = None

        elif info in dnd_external_targets and destination_tid:
            f = dnd_external_targets[info][1]

            src_model = context.get_source_widget().get_model()
            dragged_iters.append(src_model.get_iter_from_string(iter))


    for dragged_iter in dragged_iters:
        if info == 0:
            if dragged_iter and model.iter_is_valid(dragged_iter):
                dragged_tid = model.get_value(dragged_iter, 0)
                try:
                    row = []
                    for i in range(model.get_n_columns()):
                        row.append(model.get_value(dragged_iter, i))
                    #tree.move_node(dragged_tid, new_parent_id=destination_tid)
                    print ("move_after(%s, %s) ~ (%s, %s)" % (dragged_iter, destination_iter, dragged_tid, destination_tid))
                    #model.move_after(dragged_iter, destination_iter)
                    model.insert(destination_iter, -1, row)
                    model.remove(dragged_iter)
                except:
                    print('Problem with dragging: %s' % e)
        elif info in dnd_external_targets and destination_tid:    
            source = src_model.get_value(dragged_iter,0)
            # Handle external Drag'n'Drop
            f(source, destination_tid)


dnd_internal_target = 'gtg/task-iter-str'
__init_dnd()
tv.connect('drag_data_get', on_drag_data_get)
tv.connect('drag_data_received', on_drag_data_received)
tv.connect('drag_failed', on_drag_fail)

window.add(tv)
window.show_all()

tv.expand_all()
Gtk.main()
