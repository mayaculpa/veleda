from graphene import ObjectType, Schema, Field
from graphene_django.debug import DjangoDebug
from iot.graphql.schema import Query as FarmsQuery
from iot.graphql.schema import Mutation as FarmsMutation
from greenhouse.graphql.schema import Query as GreenhouseQuery


class Query(FarmsQuery, GreenhouseQuery, ObjectType):
    debug = Field(DjangoDebug, name='_debug')



class Mutation(FarmsMutation, ObjectType):
    pass


schema = Schema(query=Query, mutation=Mutation)
