class Router:
    """A router to control all database operations for webbooks"""

    db = 'webbooksdb'

    route_app_labels = {"webbooks"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.db
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self.db
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels
            or obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == self.db:
            if app_label in self.route_app_labels:
                return True
            else:
                return False
        return None
