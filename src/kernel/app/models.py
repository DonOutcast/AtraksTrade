from django.db import models


class Operator(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class PhoneQuerySet(models.QuerySet):
    def find_number(self, num: int):
        return (
            self.filter(begin__lte=num, end__gte=num)
            .select_related("operator", "region")
            .order_by("-begin")
            .first()
        )


class Phone(models.Model):
    begin = models.BigIntegerField(db_index=True)
    end = models.BigIntegerField(db_index=True)
    operator = models.ForeignKey(Operator, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    objects = PhoneQuerySet.as_manager()

    def __str__(self):
        return f"{self.begin}-{self.end}"

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(begin__lte=models.F("end")),
                name="phone_begin_lte_end",
            ),
        ]
        indexes = [
            models.Index(fields=["begin", "end"]),
        ]
        ordering = ["begin"]

    @staticmethod
    def find(num):
        return Phone.objects.filter(begin__lte=num, end__gte=num).select_related().first()
