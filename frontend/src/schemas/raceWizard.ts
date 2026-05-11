import { z } from 'zod';

const futureDateField = z
  .string()
  .min(1, 'Election date is required.')
  .refine((value) => {
    const parsedDate = new Date(value);
    return Number.isFinite(parsedDate.getTime()) && parsedDate.getTime() > Date.now();
  }, 'Must be a future date');

const optionalUrlField = z.union([z.string().trim().url('Enter a valid URL.'), z.literal('')]).optional();

export const step1Schema = z.object({
  race_type: z.enum(['candidate', 'measure'], {
    required_error: 'Select a race type.',
  }),
});

export const step2CandidateSchema = z.object({
  office_title: z.string().trim().min(3, 'Office title must be at least 3 characters.'),
  jurisdiction: z.enum(['city', 'town', 'county', 'district'], {
    required_error: 'Select a jurisdiction.',
  }),
  election_date: futureDateField,
  location_name: z.string().trim().min(1, 'Location name is required.'),
});

export const step2MeasureSchema = z.object({
  ballot_type: z.enum(['Citizen-Initiated', 'Town-Initiated'], {
    required_error: 'Select a ballot type.',
  }),
  question_title: z.string().trim().min(10, 'Question title must be at least 10 characters.'),
  election_date: futureDateField,
  location_name: z.string().trim().min(1, 'Location name is required.'),
});

export const candidateSchema = z.object({
  name: z.string().trim().min(1, 'Candidate name is required.'),
  party: z.string().trim().optional(),
  description: z.string().trim().optional(),
  image_url: optionalUrlField,
  website_url: optionalUrlField,
  candidate_type: z.enum(['running', 'write_in']),
});

export const step3CandidateSchema = z
  .object({
    candidates: z.array(candidateSchema).min(1, 'Add at least one candidate.').max(10, 'Maximum 10 candidates reached'),
  })
  .superRefine((value, context) => {
    const seenNames = new Map<string, number>();

    value.candidates.forEach((candidate, index) => {
      const normalizedName = candidate.name.trim().toLowerCase();
      if (!normalizedName) {
        return;
      }

      const existingIndex = seenNames.get(normalizedName);
      if (existingIndex !== undefined) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Candidate names must be unique.',
          path: ['candidates', existingIndex, 'name'],
        });
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Candidate names must be unique.',
          path: ['candidates', index, 'name'],
        });
        return;
      }

      seenNames.set(normalizedName, index);
    });
  });

export const step3MeasureSchema = z.object({
  yes_vote_details: z.string().trim().min(1, 'Yes-vote details are required.'),
  no_vote_details: z.string().trim().min(1, 'No-vote details are required.'),
  source_links: z.array(z.string().trim().url('Enter a valid URL.')),
});

export type Step1Values = z.infer<typeof step1Schema>;
export type Step2CandidateValues = z.infer<typeof step2CandidateSchema>;
export type Step2MeasureValues = z.infer<typeof step2MeasureSchema>;
export type Step3CandidateValues = z.infer<typeof step3CandidateSchema>;
export type Step3MeasureValues = z.infer<typeof step3MeasureSchema>;
