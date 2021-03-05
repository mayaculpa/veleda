from graphene import ObjectType, Schema, Field
from graphene_django.debug import DjangoDebug
from iot.graphql.schema import Query as IoTQuery
from iot.graphql.schema import Mutation as IoTMutation
from greenhouse.graphql.schema import Query as GreenhouseQuery
from greenhouse.graphql.schema import Mutation as GreenhouseMutation


class Query(IoTQuery, GreenhouseQuery, ObjectType):
    debug = Field(DjangoDebug, name="_debug")


class Mutation(IoTMutation, GreenhouseMutation, ObjectType):
    pass


schema = Schema(query=Query, mutation=Mutation)
