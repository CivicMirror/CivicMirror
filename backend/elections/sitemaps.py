from django.contrib.sitemaps import Sitemap

from .models import Race


class BaseSitemap(Sitemap):
    protocol = 'https'

    def get_domain(self, site=None):
        return 'civicmirror.app'


class RaceSitemap(BaseSitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return (
            Race.public_objects
            .filter(race_status__in=['active', 'archived'])
            .defer(
                'community_status', 'submitter_id', 'submitted_at',
                'moderator_notes', 'reviewed_at', 'reviewed_by_id',
                'rejection_reason', 'external_race_id',
            )
            .order_by('id')
        )

    def location(self, obj):
        return f'/races/{obj.id}'

    def lastmod(self, obj):
        return obj.last_synced_at


class StaticViewSitemap(BaseSitemap):
    priority = 1.0
    changefreq = 'weekly'

    def items(self):
        return [
            ('/', 1.0),
            ('/coverage', 0.9),
            ('/register', 0.7),
        ]

    def location(self, item):
        return item[0]

    def priority(self, item):
        return item[1]
