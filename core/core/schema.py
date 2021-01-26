from graphene import ObjectType, Schema
from farms.graphql.schema import Query as FarmsQuery
from farms.graphql.schema import Mutation as FarmsMutation


class Query(FarmsQuery, ObjectType):
    pass


class Mutation(FarmsMutation, ObjectType):
    pass


schema = Schema(query=Query, mutation=Mutation)
