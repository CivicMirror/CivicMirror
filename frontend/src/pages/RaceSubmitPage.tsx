import { zodResolver } from '@hookform/resolvers/zod';
import ArrowBack from '@mui/icons-material/ArrowBack';
import Add from '@mui/icons-material/Add';
import Delete from '@mui/icons-material/Delete';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Divider,
  FormControl,
  FormControlLabel,
  FormHelperText,
  MenuItem,
  Stack,
  Step,
  StepLabel,
  Stepper,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { Controller, useFieldArray, useForm, useWatch } from 'react-hook-form';
import { Link as RouterLink } from 'react-router-dom';
import { getApiErrorMessage } from '../api/client';
import { communityRaceApi } from '../api/races';
import {
  step1Schema,
  step2CandidateSchema,
  step2MeasureSchema,
  step3CandidateSchema,
  step3MeasureSchema,
  type Step1Values,
  type Step2CandidateValues,
  type Step2MeasureValues,
  type Step3CandidateValues,
  type Step3MeasureValues,
} from '../schemas/raceWizard';
import type { CommunityRacePayload, ConflictResponse } from '../types';
import { formatDate } from '../utils/format';

const STEP_LABELS = ['Race Type', 'Race Details', 'Candidates / Measure Details', 'Review & Submit'];
const JURISDICTION_OPTIONS: Step2CandidateValues['jurisdiction'][] = ['city', 'town', 'county', 'district'];
const BALLOT_TYPE_OPTIONS: Step2MeasureValues['ballot_type'][] = ['Citizen-Initiated', 'Town-Initiated'];

const BLANK_CANDIDATE: Step3CandidateValues['candidates'][number] = {
  name: '',
  party: '',
  description: '',
  image_url: '',
  website_url: '',
  candidate_type: 'running',
};

interface WizardState {
  raceType: Step1Values;
  candidateDetails: Step2CandidateValues;
  measureDetails: Step2MeasureValues;
  candidateEntries: Step3CandidateValues;
  measureContent: Step3MeasureValues;
  acknowledged: boolean;
}

interface StepProps<TValues> {
  initialValues: TValues;
  onBack?: () => void;
  onChange: (values: TValues) => void;
  onNext: (values: TValues) => void;
}

const INITIAL_STATE: WizardState = {
  raceType: { race_type: 'candidate' },
  candidateDetails: {
    office_title: '',
    jurisdiction: 'city',
    election_date: '',
    location_name: '',
  },
  measureDetails: {
    ballot_type: 'Citizen-Initiated',
    question_title: '',
    election_date: '',
    location_name: '',
  },
  candidateEntries: { candidates: [{ ...BLANK_CANDIDATE }] },
  measureContent: { yes_vote_details: '', no_vote_details: '', source_links: [] },
  acknowledged: false,
};

function RaceTypeStep({ initialValues, onChange, onNext }: StepProps<Step1Values>) {
  const {
    control,
    handleSubmit,
    trigger,
    formState: { errors, isValid },
  } = useForm<Step1Values>({
    resolver: zodResolver(step1Schema),
    defaultValues: initialValues,
    mode: 'onChange',
  });

  const watchedValues = useWatch({ control }) as Step1Values;

  useEffect(() => {
    onChange(watchedValues);
  }, [onChange, watchedValues]);

  useEffect(() => {
    void trigger();
  }, [trigger]);

  return (
    <Stack component="form" noValidate onSubmit={handleSubmit(onNext)} spacing={3}>
      <Box>
        <Typography gutterBottom variant="h5">
          Choose a race type
        </Typography>
        <Typography color="text.secondary">
          Candidate races collect a slate of people. Ballot measures collect the question and yes/no details.
        </Typography>
      </Box>

      <Controller
        control={control}
        name="race_type"
        render={({ field }) => (
          <FormControl error={Boolean(errors.race_type)}>
            <ToggleButtonGroup
              color="primary"
              exclusive
              fullWidth
              onChange={(_, nextValue: Step1Values['race_type'] | null) => {
                if (nextValue) {
                  field.onChange(nextValue);
                }
              }}
              value={field.value}
            >
              <ToggleButton value="candidate">Candidate Race</ToggleButton>
              <ToggleButton value="measure">Ballot Measure</ToggleButton>
            </ToggleButtonGroup>
            <FormHelperText>{errors.race_type?.message}</FormHelperText>
          </FormControl>
        )}
      />

      <Stack direction="row" justifyContent="flex-end">
        <Button disabled={!isValid} type="submit" variant="contained">
          Next
        </Button>
      </Stack>
    </Stack>
  );
}

function CandidateDetailsStep({ initialValues, onBack, onChange, onNext }: StepProps<Step2CandidateValues>) {
  const {
    register,
    control,
    handleSubmit,
    trigger,
    formState: { errors, isValid },
  } = useForm<Step2CandidateValues>({
    resolver: zodResolver(step2CandidateSchema),
    defaultValues: initialValues,
    mode: 'onChange',
  });

  const watchedValues = useWatch({ control }) as Step2CandidateValues;

  useEffect(() => {
    onChange(watchedValues);
  }, [onChange, watchedValues]);

  useEffect(() => {
    void trigger();
  }, [trigger]);

  return (
    <Stack component="form" noValidate onSubmit={handleSubmit(onNext)} spacing={2.5}>
      <TextField
        error={Boolean(errors.office_title)}
        fullWidth
        helperText={errors.office_title?.message}
        label="Office title"
        {...register('office_title')}
      />

      <TextField
        error={Boolean(errors.jurisdiction)}
        fullWidth
        helperText={errors.jurisdiction?.message}
        label="Jurisdiction"
        select
        {...register('jurisdiction')}
      >
        {JURISDICTION_OPTIONS.map((option) => (
          <MenuItem key={option} value={option}>
            {option.charAt(0).toUpperCase() + option.slice(1)}
          </MenuItem>
        ))}
      </TextField>

      <TextField
        error={Boolean(errors.election_date)}
        fullWidth
        helperText={errors.election_date?.message}
        label="Election date"
        type="date"
        InputLabelProps={{ shrink: true }}
        {...register('election_date')}
      />

      <TextField
        error={Boolean(errors.location_name)}
        fullWidth
        helperText={errors.location_name?.message}
        label="Location name"
        {...register('location_name')}
      />

      <Stack direction="row" justifyContent="space-between">
        <Button onClick={onBack} type="button">
          Back
        </Button>
        <Button disabled={!isValid} type="submit" variant="contained">
          Next
        </Button>
      </Stack>
    </Stack>
  );
}

function MeasureDetailsStep({ initialValues, onBack, onChange, onNext }: StepProps<Step2MeasureValues>) {
  const {
    register,
    control,
    handleSubmit,
    trigger,
    formState: { errors, isValid },
  } = useForm<Step2MeasureValues>({
    resolver: zodResolver(step2MeasureSchema),
    defaultValues: initialValues,
    mode: 'onChange',
  });

  const watchedValues = useWatch({ control }) as Step2MeasureValues;

  useEffect(() => {
    onChange(watchedValues);
  }, [onChange, watchedValues]);

  useEffect(() => {
    void trigger();
  }, [trigger]);

  return (
    <Stack component="form" noValidate onSubmit={handleSubmit(onNext)} spacing={2.5}>
      <TextField
        error={Boolean(errors.ballot_type)}
        fullWidth
        helperText={errors.ballot_type?.message}
        label="Ballot type"
        select
        {...register('ballot_type')}
      >
        {BALLOT_TYPE_OPTIONS.map((option) => (
          <MenuItem key={option} value={option}>
            {option}
          </MenuItem>
        ))}
      </TextField>

      <TextField
        error={Boolean(errors.question_title)}
        fullWidth
        helperText={errors.question_title?.message}
        label="Question title"
        minRows={3}
        multiline
        {...register('question_title')}
      />

      <TextField
        error={Boolean(errors.election_date)}
        fullWidth
        helperText={errors.election_date?.message}
        label="Election date"
        type="date"
        InputLabelProps={{ shrink: true }}
        {...register('election_date')}
      />

      <TextField
        error={Boolean(errors.location_name)}
        fullWidth
        helperText={errors.location_name?.message}
        label="Location name"
        {...register('location_name')}
      />

      <Stack direction="row" justifyContent="space-between">
        <Button onClick={onBack} type="button">
          Back
        </Button>
        <Button disabled={!isValid} type="submit" variant="contained">
          Next
        </Button>
      </Stack>
    </Stack>
  );
}

function CandidateEntriesStep({ initialValues, onBack, onChange, onNext }: StepProps<Step3CandidateValues>) {
  const {
    register,
    control,
    handleSubmit,
    trigger,
    formState: { errors, isValid },
  } = useForm<Step3CandidateValues>({
    resolver: zodResolver(step3CandidateSchema),
    defaultValues: initialValues,
    mode: 'onChange',
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'candidates' });
  const watchedValues = useWatch({ control }) as Step3CandidateValues;

  useEffect(() => {
    onChange(watchedValues);
  }, [onChange, watchedValues]);

  useEffect(() => {
    void trigger();
  }, [trigger]);

  return (
    <Stack component="form" noValidate onSubmit={handleSubmit(onNext)} spacing={2.5}>
      <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5} justifyContent="space-between">
        <Box>
          <Typography gutterBottom variant="h5">
            Candidates
          </Typography>
          <Typography color="text.secondary">Add up to 10 candidates, including any write-in entries.</Typography>
        </Box>
        <Button
          disabled={fields.length >= 10}
          onClick={() => append({ ...BLANK_CANDIDATE })}
          startIcon={<Add />}
          type="button"
          variant="outlined"
        >
          Add candidate
        </Button>
      </Stack>

      {fields.length >= 10 ? <Alert severity="info">Maximum 10 candidates reached</Alert> : null}

      <Stack spacing={2}>
        {fields.map((field, index) => (
          <Card key={field.id} variant="outlined">
            <CardContent sx={{ p: 2.5 }}>
              <Stack spacing={2}>
                <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5} justifyContent="space-between">
                  <Typography variant="h6">Candidate {index + 1}</Typography>
                  <Button
                    color="error"
                    disabled={fields.length === 1}
                    onClick={() => remove(index)}
                    startIcon={<Delete />}
                    type="button"
                  >
                    Remove
                  </Button>
                </Stack>

                <TextField
                  error={Boolean(errors.candidates?.[index]?.name)}
                  fullWidth
                  helperText={errors.candidates?.[index]?.name?.message}
                  label="Name"
                  {...register(`candidates.${index}.name`)}
                />

                <TextField
                  error={Boolean(errors.candidates?.[index]?.party)}
                  fullWidth
                  helperText={errors.candidates?.[index]?.party?.message}
                  label="Party"
                  {...register(`candidates.${index}.party`)}
                />

                <TextField
                  error={Boolean(errors.candidates?.[index]?.description)}
                  fullWidth
                  helperText={errors.candidates?.[index]?.description?.message}
                  label="Description"
                  minRows={2}
                  multiline
                  {...register(`candidates.${index}.description`)}
                />

                <TextField
                  error={Boolean(errors.candidates?.[index]?.image_url)}
                  fullWidth
                  helperText={errors.candidates?.[index]?.image_url?.message}
                  label="Image URL"
                  {...register(`candidates.${index}.image_url`)}
                />

                <TextField
                  error={Boolean(errors.candidates?.[index]?.website_url)}
                  fullWidth
                  helperText={errors.candidates?.[index]?.website_url?.message}
                  label="Website URL"
                  {...register(`candidates.${index}.website_url`)}
                />

                <TextField
                  error={Boolean(errors.candidates?.[index]?.candidate_type)}
                  fullWidth
                  helperText={errors.candidates?.[index]?.candidate_type?.message}
                  label="Candidate type"
                  select
                  {...register(`candidates.${index}.candidate_type`)}
                >
                  <MenuItem value="running">Running</MenuItem>
                  <MenuItem value="write_in">Write-in</MenuItem>
                </TextField>
              </Stack>
            </CardContent>
          </Card>
        ))}
      </Stack>

      {typeof errors.candidates?.message === 'string' ? <Alert severity="error">{errors.candidates.message}</Alert> : null}

      <Stack direction="row" justifyContent="space-between">
        <Button onClick={onBack} type="button">
          Back
        </Button>
        <Button disabled={!isValid} type="submit" variant="contained">
          Next
        </Button>
      </Stack>
    </Stack>
  );
}

function MeasureContentStep({ initialValues, onBack, onChange, onNext }: StepProps<Step3MeasureValues>) {
  const {
    register,
    control,
    handleSubmit,
    setValue,
    trigger,
    formState: { errors, isValid },
  } = useForm<Step3MeasureValues>({
    resolver: zodResolver(step3MeasureSchema),
    defaultValues: initialValues,
    mode: 'onChange',
  });

  const watchedValues = useWatch({ control }) as Step3MeasureValues;
  const sourceLinks = watchedValues.source_links ?? [];

  useEffect(() => {
    onChange(watchedValues);
  }, [onChange, watchedValues]);

  useEffect(() => {
    void trigger();
  }, [trigger]);

  return (
    <Stack component="form" noValidate onSubmit={handleSubmit(onNext)} spacing={2.5}>
      <TextField
        error={Boolean(errors.yes_vote_details)}
        fullWidth
        helperText={errors.yes_vote_details?.message}
        label="Yes-vote details"
        minRows={4}
        multiline
        {...register('yes_vote_details')}
      />

      <TextField
        error={Boolean(errors.no_vote_details)}
        fullWidth
        helperText={errors.no_vote_details?.message}
        label="No-vote details"
        minRows={4}
        multiline
        {...register('no_vote_details')}
      />

      <Stack spacing={1.5}>
        <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5} justifyContent="space-between">
          <Typography variant="h6">Source links</Typography>
          <Button
            onClick={() => setValue('source_links', [...sourceLinks, ''], { shouldDirty: true, shouldValidate: true })}
            startIcon={<Add />}
            type="button"
            variant="outlined"
          >
            Add source link
          </Button>
        </Stack>

        {sourceLinks.length === 0 ? (
          <Typography color="text.secondary" variant="body2">
            Add links that help moderators verify this measure.
          </Typography>
        ) : (
          <Stack spacing={1.5}>
            {sourceLinks.map((_, index) => (
              <Stack key={`source-link-${index}`} direction={{ xs: 'column', sm: 'row' }} gap={1.5}>
                <TextField
                  error={Boolean(errors.source_links?.[index])}
                  fullWidth
                  helperText={errors.source_links?.[index]?.message}
                  label={`Source link ${index + 1}`}
                  {...register(`source_links.${index}`)}
                />
                <Button
                  color="error"
                  onClick={() =>
                    setValue(
                      'source_links',
                      sourceLinks.filter((_, currentIndex) => currentIndex !== index),
                      { shouldDirty: true, shouldValidate: true },
                    )
                  }
                  startIcon={<Delete />}
                  type="button"
                >
                  Remove
                </Button>
              </Stack>
            ))}
          </Stack>
        )}
      </Stack>

      <Stack direction="row" justifyContent="space-between">
        <Button onClick={onBack} type="button">
          Back
        </Button>
        <Button disabled={!isValid} type="submit" variant="contained">
          Next
        </Button>
      </Stack>
    </Stack>
  );
}

interface ReviewStepProps {
  raceType: Step1Values['race_type'];
  candidateDetails: Step2CandidateValues;
  measureDetails: Step2MeasureValues;
  candidateEntries: Step3CandidateValues;
  measureContent: Step3MeasureValues;
  acknowledged: boolean;
  onAcknowledgedChange: (value: boolean) => void;
  onBack: () => void;
  onSubmit: (forceSubmit?: boolean) => void;
  conflict: ConflictResponse | null;
  submitError: string | null;
  submitting: boolean;
}

function ReviewStep({
  raceType,
  candidateDetails,
  measureDetails,
  candidateEntries,
  measureContent,
  acknowledged,
  onAcknowledgedChange,
  onBack,
  onSubmit,
  conflict,
  submitError,
  submitting,
}: ReviewStepProps) {
  return (
    <Stack spacing={3}>
      <Box>
        <Typography gutterBottom variant="h5">
          Review your submission
        </Typography>
        <Typography color="text.secondary">
          Confirm the details below before sending this community race to moderators.
        </Typography>
      </Box>

      {submitError ? <Alert severity="error">{submitError}</Alert> : null}

      {conflict ? (
        <Alert severity="warning">
          <Stack spacing={1.5}>
            <Typography fontWeight={700}>Similar races were found. Please review before submitting.</Typography>
            <Typography variant="body2">{conflict.detail}</Typography>
            <Stack spacing={1}>
              {conflict.conflicts.map((entry) => (
                <Stack key={entry.id} spacing={0.25}>
                  <Button component={RouterLink} sx={{ justifyContent: 'flex-start', px: 0 }} to={`/races/${entry.id}`}>
                    {entry.office_title}
                  </Button>
                  <Typography color="text.secondary" variant="caption">
                    {entry.jurisdiction}
                    {entry.election_date ? ` · ${formatDate(entry.election_date)}` : ''}
                    {entry.location_name ? ` · ${entry.location_name}` : ''}
                  </Typography>
                </Stack>
              ))}
            </Stack>
          </Stack>
        </Alert>
      ) : null}

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h6">Race type</Typography>
            <Typography>{raceType === 'candidate' ? 'Candidate Race' : 'Ballot Measure'}</Typography>
          </Stack>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h6">Race details</Typography>
            {raceType === 'candidate' ? (
              <>
                <Typography>Office title: {candidateDetails.office_title}</Typography>
                <Typography>Jurisdiction: {candidateDetails.jurisdiction}</Typography>
                <Typography>Election date: {formatDate(candidateDetails.election_date)}</Typography>
                <Typography>Location: {candidateDetails.location_name}</Typography>
              </>
            ) : (
              <>
                <Typography>Ballot type: {measureDetails.ballot_type}</Typography>
                <Typography>Question title: {measureDetails.question_title}</Typography>
                <Typography>Election date: {formatDate(measureDetails.election_date)}</Typography>
                <Typography>Location: {measureDetails.location_name}</Typography>
              </>
            )}
          </Stack>
        </CardContent>
      </Card>

      <Card variant="outlined">
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h6">
              {raceType === 'candidate' ? 'Candidates' : 'Measure details'}
            </Typography>
            {raceType === 'candidate' ? (
              <Stack divider={<Divider flexItem />} spacing={1.5}>
                {candidateEntries.candidates.map((candidate, index) => (
                  <Stack key={`${candidate.name}-${index}`} spacing={0.25}>
                    <Typography fontWeight={700}>
                      {candidate.name} {candidate.candidate_type === 'write_in' ? '(Write-in)' : ''}
                    </Typography>
                    {candidate.party ? <Typography color="text.secondary">Party: {candidate.party}</Typography> : null}
                    {candidate.description ? <Typography color="text.secondary">{candidate.description}</Typography> : null}
                    {candidate.website_url ? <Typography color="text.secondary">Website: {candidate.website_url}</Typography> : null}
                    {candidate.image_url ? <Typography color="text.secondary">Image: {candidate.image_url}</Typography> : null}
                  </Stack>
                ))}
              </Stack>
            ) : (
              <Stack spacing={1}>
                <Typography>Yes-vote details: {measureContent.yes_vote_details}</Typography>
                <Typography>No-vote details: {measureContent.no_vote_details}</Typography>
                <Typography>
                  Source links: {measureContent.source_links.length > 0 ? measureContent.source_links.join(', ') : 'None provided'}
                </Typography>
              </Stack>
            )}
          </Stack>
        </CardContent>
      </Card>

      <FormControl required>
        <FormControlLabel
          control={<Checkbox checked={acknowledged} onChange={(event) => onAcknowledgedChange(event.target.checked)} />}
          label="I understand this submission will be reviewed by moderators before appearing publicly."
        />
        {!acknowledged ? (
          <FormHelperText>You must acknowledge moderation review before submitting.</FormHelperText>
        ) : null}
      </FormControl>

      <Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5} justifyContent="space-between">
        <Button onClick={onBack} type="button">
          Back
        </Button>
        <Button
          disabled={!acknowledged || submitting}
          onClick={() => onSubmit(Boolean(conflict))}
          variant="contained"
        >
          {conflict ? 'Submit Anyway' : 'Submit'}
        </Button>
      </Stack>
    </Stack>
  );
}

function RaceSubmitPage() {
  const [activeStep, setActiveStep] = useState(0);
  const [wizardState, setWizardState] = useState<WizardState>(INITIAL_STATE);
  const [conflict, setConflict] = useState<ConflictResponse | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submittedId, setSubmittedId] = useState<number | null>(null);

  const payload = useMemo<CommunityRacePayload>(() => {
    if (wizardState.raceType.race_type === 'candidate') {
      return {
        race_type: 'candidate',
        office_title: wizardState.candidateDetails.office_title.trim(),
        jurisdiction: wizardState.candidateDetails.jurisdiction,
        election_date: wizardState.candidateDetails.election_date,
        location_name: wizardState.candidateDetails.location_name.trim(),
        candidates: wizardState.candidateEntries.candidates.map((candidate) => ({
          name: candidate.name.trim(),
          party: candidate.party?.trim() || undefined,
          description: candidate.description?.trim() || undefined,
          image_url: candidate.image_url?.trim() || undefined,
          website_url: candidate.website_url?.trim() || undefined,
          candidate_type: candidate.candidate_type,
        })),
      };
    }

    return {
      race_type: 'measure',
      ballot_type: wizardState.measureDetails.ballot_type,
      question_title: wizardState.measureDetails.question_title.trim(),
      election_date: wizardState.measureDetails.election_date,
      location_name: wizardState.measureDetails.location_name.trim(),
      yes_vote_details: wizardState.measureContent.yes_vote_details.trim(),
      no_vote_details: wizardState.measureContent.no_vote_details.trim(),
      source_links: wizardState.measureContent.source_links.map((link) => link.trim()),
    };
  }, [wizardState]);

  const clearSubmissionState = () => {
    setConflict(null);
    setSubmitError(null);
  };

  const handleSubmit = async (forceSubmit = false) => {
    clearSubmissionState();
    setSubmitting(true);

    try {
      const response = await communityRaceApi.submitCommunityRace({
        ...payload,
        ...(forceSubmit ? { force_submit: true } : {}),
      });

      if ('conflict' in response && response.conflict) {
        setConflict(response);
        return;
      }

      if ('id' in response) {
        const responseId = Number(response.id);
        if (Number.isFinite(responseId)) {
          setSubmittedId(responseId);
        }
      }
    } catch (error) {
      setSubmitError(getApiErrorMessage(error, 'We could not submit this race right now.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (submittedId) {
    return (
      <Stack spacing={3}>
        <Button component={RouterLink} startIcon={<ArrowBack />} sx={{ alignSelf: 'flex-start' }} to="/">
          Back to races
        </Button>
        <Card>
          <CardContent sx={{ p: { xs: 3, md: 5 } }}>
            <Stack spacing={2.5}>
              <Typography variant="h4">Submission received</Typography>
              <Alert severity="success">
                ✅ Your race has been submitted for review. It will appear publicly once approved by a moderator.
              </Alert>
              <Typography color="text.secondary">Submission reference: #{submittedId}</Typography>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    );
  }

  return (
    <Stack spacing={3.5}>
      <Button component={RouterLink} startIcon={<ArrowBack />} sx={{ alignSelf: 'flex-start' }} to="/">
        Back to race browser
      </Button>

      <Card>
        <CardContent sx={{ p: { xs: 3, md: 5 } }}>
          <Stack spacing={3.5}>
            <Box>
              <Typography gutterBottom variant="h4">
                Submit a local race
              </Typography>
              <Typography color="text.secondary">
                Help fill in missing local contests. Every submission is reviewed by moderators before it can appear publicly.
              </Typography>
            </Box>

            <Stepper activeStep={activeStep} alternativeLabel>
              {STEP_LABELS.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>

            {activeStep === 0 ? (
              <RaceTypeStep
                initialValues={wizardState.raceType}
                onChange={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, raceType: values }));
                }}
                onNext={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, raceType: values }));
                  setActiveStep(1);
                }}
              />
            ) : null}

            {activeStep === 1 && wizardState.raceType.race_type === 'candidate' ? (
              <CandidateDetailsStep
                initialValues={wizardState.candidateDetails}
                onBack={() => setActiveStep(0)}
                onChange={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, candidateDetails: values }));
                }}
                onNext={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, candidateDetails: values }));
                  setActiveStep(2);
                }}
              />
            ) : null}

            {activeStep === 1 && wizardState.raceType.race_type === 'measure' ? (
              <MeasureDetailsStep
                initialValues={wizardState.measureDetails}
                onBack={() => setActiveStep(0)}
                onChange={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, measureDetails: values }));
                }}
                onNext={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, measureDetails: values }));
                  setActiveStep(2);
                }}
              />
            ) : null}

            {activeStep === 2 && wizardState.raceType.race_type === 'candidate' ? (
              <CandidateEntriesStep
                initialValues={wizardState.candidateEntries}
                onBack={() => setActiveStep(1)}
                onChange={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, candidateEntries: values }));
                }}
                onNext={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, candidateEntries: values }));
                  setActiveStep(3);
                }}
              />
            ) : null}

            {activeStep === 2 && wizardState.raceType.race_type === 'measure' ? (
              <MeasureContentStep
                initialValues={wizardState.measureContent}
                onBack={() => setActiveStep(1)}
                onChange={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, measureContent: values }));
                }}
                onNext={(values) => {
                  clearSubmissionState();
                  setWizardState((currentState) => ({ ...currentState, measureContent: values }));
                  setActiveStep(3);
                }}
              />
            ) : null}

            {activeStep === 3 ? (
              <ReviewStep
                acknowledged={wizardState.acknowledged}
                candidateDetails={wizardState.candidateDetails}
                candidateEntries={wizardState.candidateEntries}
                conflict={conflict}
                measureContent={wizardState.measureContent}
                measureDetails={wizardState.measureDetails}
                onAcknowledgedChange={(value) =>
                  setWizardState((currentState) => ({ ...currentState, acknowledged: value }))
                }
                onBack={() => setActiveStep(2)}
                onSubmit={(forceSubmit) => {
                  void handleSubmit(forceSubmit);
                }}
                raceType={wizardState.raceType.race_type}
                submitError={submitError}
                submitting={submitting}
              />
            ) : null}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

export default RaceSubmitPage;
