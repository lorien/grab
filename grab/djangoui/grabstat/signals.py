from django.db.models.signals import post_save
from django.dispatch import receive # noqa


@receiver(post_save, sender=Foo)
def foo_post_save(instance, **kwargs):
    pass
