from graphene_django import DjangoObjectType
import graphene

from accounts.models import User, Profile


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        filter_fields = {"email": ["exact"]}
        fields = ("email", "profile")

    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(pk=info.context.user.pk)


class ProfileNode(DjangoObjectType):
    class Meta:
        model = Profile
        interfaces = (graphene.relay.Node,)
        filter_fields = {"short_name": ["exact"], "full_name": ["exact"]}
        fields = ("user", "short_name", "full_name")
    
    @classmethod
    def get_queryset(cls, queryset, info):
        return queryset.filter(user=info.context.user)
