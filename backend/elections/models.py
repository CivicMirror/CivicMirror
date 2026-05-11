from django.conf import settings
from django.db import models


class PublicRaceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            ~models.Q(source='community') | models.Q(source='community', community_status='active')
        )


class CommunityRaceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(source='community')


class Election(models.Model):
    class JurisdictionLevel(models.TextChoices):
        NATIONAL = 'national', 'National'
        STATE = 'state', 'State'
        LOCAL = 'local', 'Local'

    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ACTIVE = 'active', 'Active'
        RESULTS_PENDING = 'results_pending', 'Results Pending'
        RESULTS_CERTIFIED = 'results_certified', 'Results Certified'
        ARCHIVED = 'archived', 'Archived'

    name = models.CharField(max_length=255)
    election_date = models.DateField()
    jurisdiction_level = models.CharField(max_length=20, choices=JurisdictionLevel.choices)
    state = models.CharField(max_length=2, null=True, blank=True)
    source_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=30, default=Status.UPCOMING, choices=Status.choices)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['source_id'])]
        ordering = ['election_date', 'name']

    def __str__(self) -> str:
        return f'{self.name} ({self.election_date})'


class Race(models.Model):
    class RaceType(models.TextChoices):
        CANDIDATE = 'candidate', 'Candidate'
        MEASURE = 'measure', 'Measure'

    class CertificationStatus(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        RESULTS_PENDING = 'results_pending', 'Results Pending'
        RESULTS_CERTIFIED = 'results_certified', 'Results Certified'
        PARTIAL_RESULTS = 'partial_results', 'Partial Results'

    class Source(models.TextChoices):
        CIVIC_API = 'civic_api', 'Civic API'
        COMMUNITY = 'community', 'Community'

    class CommunityStatus(models.TextChoices):
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        ACTIVE = 'active', 'Active'
        REJECTED = 'rejected', 'Rejected'

    class RaceStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        ACTIVE = 'active', 'Active'
        CANCELLED = 'cancelled', 'Cancelled'
        ARCHIVED = 'archived', 'Archived'

    class VoteMethod(models.TextChoices):
        SINGLE_CHOICE = 'single_choice', 'Single Choice'
        MULTI_SEAT = 'multi_seat', 'Multi Seat'
        RANKED_CHOICE = 'ranked_choice', 'Ranked Choice'
        YES_NO = 'yes_no', 'Yes / No'

    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='races')
    race_type = models.CharField(max_length=20, choices=RaceType.choices)
    office_title = models.CharField(max_length=255)
    jurisdiction = models.CharField(max_length=255)
    geography_scope = models.CharField(max_length=50)
    voting_opens = models.DateTimeField(null=True, blank=True)
    voting_closes = models.DateTimeField(null=True, blank=True)
    certification_status = models.CharField(max_length=30, default=CertificationStatus.UPCOMING, choices=CertificationStatus.choices)
    source = models.CharField(max_length=20, choices=Source.choices)
    community_status = models.CharField(max_length=20, choices=CommunityStatus.choices, null=True, blank=True)
    submitter = models.ForeignKey('accounts.UserProfile', null=True, blank=True, on_delete=models.SET_NULL, related_name='submitted_races')
    submitted_at = models.DateTimeField(null=True, blank=True)
    source_links = models.JSONField(default=list, blank=True)
    location_name = models.CharField(max_length=255, blank=True)
    moderator_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_races')
    rejection_reason = models.TextField(blank=True)
    race_status = models.CharField(max_length=20, default=RaceStatus.ACTIVE, choices=RaceStatus.choices)
    vote_method = models.CharField(max_length=20, default=VoteMethod.SINGLE_CHOICE, choices=VoteMethod.choices)
    max_selections = models.PositiveIntegerField(default=1)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    ocd_division_id = models.CharField(max_length=255, blank=True)
    normalized_office_title = models.CharField(max_length=255, blank=True)
    canonical_key = models.CharField(max_length=512, unique=True, null=True, blank=True)
    ballot_type = models.CharField(max_length=100, blank=True)
    yes_vote_details = models.TextField(blank=True)
    no_vote_details = models.TextField(blank=True)
    supporting_links = models.JSONField(default=list, blank=True)

    objects = models.Manager()
    public_objects = PublicRaceManager()

    class Meta:
        indexes = [
            models.Index(fields=['election', 'race_status', 'certification_status']),
            models.Index(fields=['geography_scope']),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(max_selections__gte=1), name='race_max_selections_gte_1')
        ]
        ordering = ['office_title']

    def save(self, *args, **kwargs):
        if self.office_title and not self.normalized_office_title:
            self.normalized_office_title = ' '.join(self.office_title.strip().lower().split())
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.office_title} - {self.election.name}'


class Candidate(models.Model):
    class CandidateStatus(models.TextChoices):
        RUNNING = 'running', 'Running'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        DISQUALIFIED = 'disqualified', 'Disqualified'
        WRITE_IN = 'write_in', 'Write-in'

    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=255)
    party = models.CharField(max_length=100, blank=True)
    incumbent = models.BooleanField(default=False)
    candidate_status = models.CharField(max_length=20, default=CandidateStatus.RUNNING, choices=CandidateStatus.choices)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['race', 'name'], name='unique_candidate_name_per_race')
        ]
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class MeasureOption(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='measure_options')
    option_label = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['race', 'option_label'], name='unique_measure_option_per_race')
        ]
        ordering = ['id']

    def __str__(self) -> str:
        return f'{self.option_label} ({self.race.office_title})'


class CommunityRace(Race):
    objects = CommunityRaceManager()

    class Meta:
        proxy = True
        verbose_name = 'Community race'
        verbose_name_plural = 'Community races'
        ordering = ['submitted_at']
