from django.db import models

class Initiative(TimeStampMixin, UUIDMixin):
    INITIATIVE_STATUS = (
        (1, "Active"),
        (2, "Completed"),
        (3, "Draft"),
        (4, "Cancelled"),
    )
    name = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.IntegerField(choices=INITIATIVE_STATUS, default=1)
    video_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_available_tasks_count(self):
        return self.task_set.filter(status=Task.TASK_STATUS_AVAILABLE).count()

    def get_completed_task_count(self):
        return self.task_set.filter(status=Task.TASK_STATUS_DONE).count()

    def get_task_tags(self):
        return Tag.objects.filter(task_tags__initiative=self).distinct("id").all()

    @staticmethod
    def get_filtered_data(input_data, filter_data=None, exclude_data=None):
        if filter_data is None:
            filter_data = {}
        if not filter_data:
            filter_data = dict()

        if not input_data:
            input_data = dict()

        statuses = input_data.get("statuses", [])
        tags = input_data.get("tags", [])
        categories = input_data.get("categories", None)

        if statuses:
            filter_data["status__in"] = statuses

        if tags:
            filter_data["task__tag__in"] = tags

        if categories:
            filter_data["task__category__parent__in"] = categories

        queryset = Initiative.objects.filter(**filter_data)
        if exclude_data:
            queryset = queryset.exclude(**exclude_data)

        return queryset.distinct("id").all()


@receiver(post_save, sender=Initiative)
def save_initiative(sender, instance, created, **kwargs):
    if not created:
        # update tasklisting when initiative info is updated
        ChallengeListing.objects.filter(initiative=instance).update(initiative_data=to_dict(instance))

