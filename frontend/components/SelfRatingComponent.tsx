import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';

interface CSSEFCriterion {
  id: string;
  title: string;
  description: string;
}

interface RatingData {
  score: number | null;
  comment: string;
}

interface SelfRatingData {
  ratings: Record<string, RatingData>;
  overall_comment: string;
  confidence_level: number | null;
}

interface SelfRatingComponentProps {
  onChange: (data: SelfRatingData, isComplete: boolean) => void;
  onCancel?: () => void;
  initialData?: SelfRatingData | null;
  isLoading?: boolean;
  context?: string;
}

const CSSEF_CRITERIA: CSSEFCriterion[] = [
  {
    id: 'C1_topic_choice',
    title: 'Topic Choice & Focus',
    description: 'Chooses and narrows a topic appropriately for the audience & occasion'
  },
  {
    id: 'C2_purpose',
    title: 'Thesis & Purpose',
    description: 'Communicates the thesis/specific purpose in a manner appropriate for the audience & occasion'
  },
  {
    id: 'C3_supporting_material',
    title: 'Supporting Materials',
    description: 'Provides supporting material appropriate for the audience & occasion'
  },
  {
    id: 'C4_organization',
    title: 'Organization & Structure',
    description: 'Uses an organizational pattern appropriate to the topic, audience, occasion, & purpose'
  },
  {
    id: 'C5_language_use',
    title: 'Language Use',
    description: 'Uses language appropriate to the audience & occasion'
  },
  {
    id: 'C6_vocal_variety',
    title: 'Vocal Variety & Delivery',
    description: 'Uses vocal variety in rate, pitch, & intensity to heighten & maintain interest'
  },
  {
    id: 'C7_pronunciation_and_grammar',
    title: 'Pronunciation & Grammar',
    description: 'Uses pronunciation, grammar, & articulation appropriate to the audience & occasion'
  },
  {
    id: 'C8_physical_behaviors',
    title: 'Physical Behaviors',
    description: 'Uses physical behaviors that support the verbal message'
  }
];

const StarRating: React.FC<{
  rating: number | null;
  onRatingChange: (rating: number) => void;
  size?: 'sm' | 'md' | 'lg';
}> = ({ rating, onRatingChange, size = 'md' }) => {
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);
  
  const starSize = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-8 h-8' : 'w-6 h-6';
  
  return (
    <div className="flex items-center space-x-1">
      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((star) => (
        <button
          key={star}
          type="button"
          className={`${starSize} transition-colors duration-150 ${
            (hoveredRating !== null ? star <= hoveredRating : star <= (rating || 0))
              ? 'text-yellow-400'
              : 'text-gray-300'
          } hover:text-yellow-400`}
          onMouseEnter={() => setHoveredRating(star)}
          onMouseLeave={() => setHoveredRating(null)}
          onClick={() => onRatingChange(star)}
        >
          <svg fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </button>
      ))}
      <span className="ml-2 text-sm text-gray-600 min-w-[3rem]">
        {rating ? `${rating}/10` : 'Not rated'}
      </span>
    </div>
  );
};

const SelfRatingComponent: React.FC<SelfRatingComponentProps> = ({
  onChange,
  onCancel,
  initialData,
  isLoading = false,
  context = 'general'
}) => {
  const [formData, setFormData] = useState<SelfRatingData>({
    ratings: {},
    overall_comment: '',
    confidence_level: null
  });

  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize form data
  useEffect(() => {
    // Always initialize with empty ratings for all criteria first
    const emptyRatings: Record<string, RatingData> = {};
    CSSEF_CRITERIA.forEach(criterion => {
      emptyRatings[criterion.id] = { score: null, comment: '' };
    });
    
    let initialFormData: SelfRatingData = {
      ratings: emptyRatings,
      overall_comment: '',
      confidence_level: null
    };
    
    // If initialData is provided, merge it with the empty structure
    if (initialData) {
      initialFormData = {
        ...initialFormData,
        overall_comment: initialData.overall_comment || '',
        confidence_level: initialData.confidence_level || null,
        ratings: { ...emptyRatings } // Start with empty ratings
      };
      
      // Merge only existing ratings from initialData
      if (initialData.ratings) {
        Object.keys(initialData.ratings).forEach(criterionId => {
          if (emptyRatings[criterionId]) {
            const initialRating = initialData.ratings[criterionId];
            initialFormData.ratings[criterionId] = {
              score: initialRating?.score || null,
              comment: initialRating?.comment || ''
            };
          }
        });
      }
    }
    
    setFormData(initialFormData);
    setIsInitialized(true);
  }, [initialData]);

  const updateRating = (criterionId: string, field: 'score' | 'comment', value: number | string) => {
    setFormData(prev => ({
      ...prev,
      ratings: {
        ...prev.ratings,
        [criterionId]: {
          ...prev.ratings[criterionId],
          [field]: value
        }
      }
    }));
  };

  const updateConfidenceLevel = (value: number) => {
    setFormData(prev => ({
      ...prev,
      confidence_level: value
    }));
  };

  const updateOverallComment = (value: string) => {
    setFormData(prev => ({
      ...prev,
      overall_comment: value
    }));
  };

  const validateForm = (): boolean => {
    const errors: string[] = [];
    
    // Check if at least 3 criteria have been rated
    const ratedCriteria = Object.values(formData.ratings).filter(rating => rating.score !== null);
    if (ratedCriteria.length < 3) {
      errors.push('Please rate at least 3 criteria to continue');
    }
    
    // Check confidence level
    if (formData.confidence_level === null) {
      errors.push('Please indicate your confidence level');
    }
    
    setValidationErrors(errors);
    return errors.length === 0;
  };

  // Check if form is complete and notify parent component
  useEffect(() => {
    if (!isInitialized) return; // Don't call onChange until initialized
    
    const isComplete = validateForm();
    onChange(formData, isComplete);
  }, [formData, isInitialized]); // Removed onChange from dependencies

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Rate Your Speech Performance</h2>
        <p className="text-gray-600">
          Before we analyze your speech with AI, please rate yourself on the CSSEF criteria.
          This helps us understand your self-perception and provides valuable research data.
        </p>
        {context && context !== 'general' && (
          <div className="mt-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full inline-block text-sm">
            Context: {context.charAt(0).toUpperCase() + context.slice(1)}
          </div>
        )}
      </div>

      {validationErrors.length > 0 && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <h4 className="text-red-800 font-medium mb-1">Please fix the following issues:</h4>
          <ul className="text-red-700 text-sm list-disc list-inside">
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="space-y-6">
        {/* CSSEF Criteria Ratings */}
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
            CSSEF Criteria (Rate 1-10)
          </h3>
          
          {CSSEF_CRITERIA.map((criterion) => (
            <div key={criterion.id} className="border border-gray-200 rounded-lg p-4">
              <div className="mb-3">
                <h4 className="font-medium text-gray-900 mb-1">{criterion.title}</h4>
                <p className="text-sm text-gray-600">{criterion.description}</p>
              </div>
              
              <div className="mb-3">
                <div className="flex items-center justify-between">
                  <StarRating
                    rating={formData.ratings[criterion.id]?.score ?? null}
                    onRatingChange={(rating) => updateRating(criterion.id, 'score', rating)}
                  />
                  <div className="text-sm text-gray-500 ml-4">
                    {formData.ratings[criterion.id]?.score ? 
                      `Score: ${formData.ratings[criterion.id].score}/10` : 
                      'Not Rated'
                    }
                  </div>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Comments (optional)
                </label>
                <textarea
                  value={formData.ratings[criterion.id]?.comment || ''}
                  onChange={(e) => updateRating(criterion.id, 'comment', e.target.value)}
                  placeholder="Any specific thoughts about this aspect of your speech..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                  rows={2}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Overall Comment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Overall Reflection (optional)
          </label>
          <textarea
            value={formData.overall_comment}
            onChange={(e) => updateOverallComment(e.target.value)}
            placeholder="How do you feel about your overall performance? What went well? What would you improve?"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            rows={3}
          />
        </div>

        {/* Confidence Level */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            How confident are you in your self-assessment? *
          </label>
          <div className="flex space-x-4">
            {[1, 2, 3, 4, 5].map((level) => (
              <label key={level} className="flex items-center">
                <input
                  type="radio"
                  name="confidence_level"
                  value={level}
                  checked={formData.confidence_level === level}
                  onChange={(e) => updateConfidenceLevel(parseInt(e.target.value))}
                  className="mr-2"
                />
                <span className="text-sm">
                  {level === 1 && 'Not confident'}
                  {level === 2 && 'Slightly confident'}
                  {level === 3 && 'Moderately confident'}
                  {level === 4 && 'Very confident'}
                  {level === 5 && 'Extremely confident'}
                </span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SelfRatingComponent;