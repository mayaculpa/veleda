from graphene import Field, ObjectType, Schema
from graphene_django.debug import DjangoDebug

from accounts.graphql.schema import Query as AccountsSchema
from greenhouse.graphql.schema import Mutation as GreenhouseMutation
from greenhouse.graphql.schema import Query as GreenhouseQuery
from iot.graphql.schema import Mutation as IoTMutation
from iot.graphql.schema import Query as IoTQuery
from iot.graphql.schema import Subscription as IoTSubscription


class Query(IoTQuery, GreenhouseQuery, AccountsSchema, ObjectType):
    debug = Field(DjangoDebug, name="_debug")


class Mutation(IoTMutation, GreenhouseMutation, ObjectType):
    pass


class Subscription(IoTSubscription, ObjectType):
    pass


schema = Schema(query=Query, mutation=Mutation, subscription=Subscription)
