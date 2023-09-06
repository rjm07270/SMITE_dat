from db import db

class my_class(object):

    @staticmethod
    def get_god_name_by_id(god_id):
        sql = f"SELECT name FROM gods WHERE id = {god_id};"
        result = db.get(sql)
        if result:
            return result[0][0]
        else:
            print(f"No god found with id {god_id}")
            return None

    @staticmethod
    def get_item_device_name(item_id=None, icon_id=None):
        if item_id:
            sql = f"SELECT DeviceName FROM items WHERE ItemId = {item_id};"
        elif icon_id:
            sql = f"SELECT DeviceName FROM items WHERE IconId = {icon_id};"
        else:
            print("Either item_id or icon_id must be provided.")
            return None

        result = db.get(sql)
        if result:
            return result[0][0]
        else:
            print(f"No item found with ItemId {item_id} or IconId {icon_id}")
            return None
        


    @staticmethod
    def get_name_by_id(id_):
        sql = f"SELECT UnifiedName FROM unified_ids WHERE UnifiedID = {id_};"
        result = db.get(sql)
        if result:
            return result[0][0]
        else:
            return f"Unknown ID: {id_}"

    @staticmethod
    def get_names_from_ids(id_list):
        names = []
        for id_ in id_list:
            name = my_class.get_name_by_id(id_)
            names.append(name)
        return names




