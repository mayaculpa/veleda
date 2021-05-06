from accounts.graphql.nodes import ProfileNode, UserNode
import graphene
from graphene_django.filter import DjangoFilterConnectionField


class Query:
    user = graphene.relay.Node.Field(UserNode)
    all_users = DjangoFilterConnectionField(UserNode)
    current_user = graphene.Field(UserNode)

    profile = graphene.relay.Node.Field(ProfileNode)
    all_profiles = DjangoFilterConnectionField(ProfileNode)

    @staticmethod
    def resolve_current_user(parent, info, **kwargs):
        return info.context.user