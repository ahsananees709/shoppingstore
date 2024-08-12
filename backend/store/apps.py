from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'
    '''
    Ye ready function tab call hota jab hmari app ki execution start hoti ha
    '''
    def ready(self) -> None:
        import store.signals
