# coding: utf-8

from django.db import models

from rels.django_staff import TableIntegerField

from game.pvp.relations import BATTLE_1X1_STATE, BATTLE_1X1_RESULT

class Battle1x1(models.Model):

    account = models.ForeignKey('accounts.Account', null=False, unique=True, related_name='+')
    enemy = models.ForeignKey('accounts.Account', null=True, unique=True, related_name='+')

    created_at = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True, null=False)

    state = TableIntegerField(relation=BATTLE_1X1_STATE, relation_column='value', db_index=True)

    calculate_rating = models.BooleanField(default=False, db_index=True)


class Battle1x1Result(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=False)

    participant_1 = models.ForeignKey('accounts.Account', null=False, related_name='+')
    participant_2 = models.ForeignKey('accounts.Account', null=False, related_name='+')

    result = TableIntegerField(relation=BATTLE_1X1_RESULT, relation_column='value', db_index=True)
