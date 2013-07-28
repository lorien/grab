from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db.models import F

#from grabstat.models import

@receiver(post_save, sender=Foo)
def foo_post_save(instance, **kwargs):
    pass
