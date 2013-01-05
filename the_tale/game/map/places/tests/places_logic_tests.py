# coding: utf-8

from django.test import TestCase

from game.map.places.prototypes import PlacePrototype
from game.map.places.models import Place, PLACE_TYPE
from game.map.places.conf import places_settings
from game.map.places.exceptions import PlacesException

from game.map.places.storage import places_storage
from game.persons.storage import persons_storage

class PlacePowerTest(TestCase):

    def setUp(self):
        places_storage.clear()
        persons_storage.clear()

        self.model = Place.objects.create(x=0,
                                          y=0,
                                          name='power_test_place',
                                          type=PLACE_TYPE.CITY,
                                          size=5 )

        self.place = PlacePrototype(self.model)
        self.place.sync_persons()

        places_storage.sync(force=True)
        persons_storage.sync(force=True)


    def test_initialization(self):
        self.assertEqual(self.place.power, 0)

    def test_push_power(self):
        self.place.push_power(0, 10)
        self.assertEqual(self.place.power, 10)

        self.place.push_power(1, 1)
        self.assertEqual(self.place.power, 11)

        self.place.push_power(places_settings.POWER_HISTORY_LENGTH-1, 100)
        self.assertEqual(self.place.power, 111)

        self.place.push_power(places_settings.POWER_HISTORY_LENGTH, 1000)
        self.assertEqual(self.place.power, 1111)

        self.place.push_power(places_settings.POWER_HISTORY_LENGTH+1, 10000)
        self.assertEqual(self.place.power, 11101)

        self.place.push_power(places_settings.POWER_HISTORY_LENGTH+2, 100000)
        self.assertEqual(self.place.power, 111100)

    def test_push_power_exceptions(self):
        self.place.push_power(666, 10)
        self.assertRaises(PlacesException, self.place.push_power, 13, 1)

    def test_persons_sorting(self):
        person_1 = self.place.persons[0]
        person_2 = self.place.persons[1]

        person_1.push_power(0, 1)
        person_1.save()

        person_2.push_power(0, 10)
        person_2.save()

        self.assertEqual([person.id for person in self.place.persons][:2],
                         [person_2.id, person_1.id])
