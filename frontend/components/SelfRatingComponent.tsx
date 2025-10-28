import React, { useState, useEffect, useCallback, useRef } from 'react';

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
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
      <div className="flex items-center flex-wrap gap-1">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((star) => (
          <button
            key={star}
            type="button"
            className={`${starSize} transition-colors duration-150 flex-shrink-0 ${
              (hoveredRating !== null ? star <= hoveredRating : star <= (rating || 0))
                ? 'text-yellow-400'
                : 'text-gray-300'
            } hover:text-yellow-400 focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:ring-opacity-50 rounded`}
            onMouseEnter={() => setHoveredRating(star)}
            onMouseLeave={() => setHoveredRating(null)}
            onClick={() => onRatingChange(star)}
            aria-label={`Rate ${star} out of 10`}
          >
            <svg fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </button>
        ))}
      </div>
      <span className="text-sm text-gray-600 font-medium min-w-[5rem] sm:ml-3">
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

  const [isInitialized, setIsInitialized] = useState(false);
  
  // Use ref to store the latest onChange function to avoid dependency issues
  const onChangeRef = useRef(onChange);
  onChangeRef.current = onChange;

  // Initialize form data - only run once on mount
  useEffect(() => {
    if (isInitialized) return; // Only initialize once
    
    // Always initialize with empty ratings for all criteria first
    const emptyRatings: Record<string, RatingData> = {};
    CSSEF_CRITERIA.forEach(criterion => {
      emptyRatings[criterion.id] = { score: null, comment: '' };
    });
    
    const initialFormData: SelfRatingData = {
      ratings: emptyRatings,
      overall_comment: '',
      confidence_level: null
    };
    
    setFormData(initialFormData);
    setIsInitialized(true);
  }, []); // Empty dependency array - only run once on mount
  
  // Separate effect to handle initialData updates only when it's meaningful
  useEffect(() => {
    if (!isInitialized || !initialData) return;
    
    // Only update if initialData has meaningful content (not just empty structure)
    const hasRatings = initialData.ratings && Object.values(initialData.ratings).some(rating => rating.score !== null);
    const hasComment = initialData.overall_comment && initialData.overall_comment.trim() !== '';
    const hasConfidence = initialData.confidence_level !== null;
    
    if (!hasRatings && !hasComment && !hasConfidence) {
      return; // Don't update for empty initialData
    }
    
    setFormData(prev => ({
      overall_comment: initialData.overall_comment || prev.overall_comment,
      confidence_level: initialData.confidence_level ?? prev.confidence_level,
      ratings: {
        ...prev.ratings,
        ...(initialData.ratings || {})
      }
    }));
  }, [initialData, isInitialized]);

  const updateRating = (criterionId: string, field: 'score' | 'comment', value: number | string) => {
    const newFormData = {
      ...formData,
      ratings: {
        ...formData.ratings,
        [criterionId]: {
          score: formData.ratings[criterionId]?.score ?? null,
          comment: formData.ratings[criterionId]?.comment ?? '',
          [field]: value
        }
      }
    };
    
    setFormData(newFormData);
    
    // Validate and notify parent immediately
    validateAndNotify(newFormData);
  };

  const updateConfidenceLevel = (value: number) => {
    const newFormData = {
      ...formData,
      confidence_level: value
    };
    
    setFormData(newFormData);
    
    // Validate and notify parent immediately
    validateAndNotify(newFormData);
  };

  const updateOverallComment = (value: string) => {
    const newFormData = {
      ...formData,
      overall_comment: value
    };
    
    setFormData(newFormData);
    
    // Validate and notify parent immediately
    validateAndNotify(newFormData);
  };

  // Simple validation function that doesn't cause re-renders
  const validateAndNotify = (data: SelfRatingData) => {
    if (!isInitialized) return;
    
    const errors: string[] = [];
    
    // Check if at least 3 criteria have been rated
    const ratedCriteria = Object.values(data.ratings).filter(rating => rating.score !== null);
    if (ratedCriteria.length < 3) {
      errors.push('Please rate at least 3 criteria to continue');
    }
    
    // Check confidence level
    if (data.confidence_level === null) {
      errors.push('Please indicate your confidence level');
    }
    
    // Just log errors for debugging - no state updates
    if (errors.length > 0) {
      console.log('Validation errors:', errors);
    }
    
    const isComplete = errors.length === 0;
    
    // Call parent onChange
    onChangeRef.current(data, isComplete);
  };

  return (
    <div className="relative bg-white border border-gray-200 rounded-lg p-6">
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg z-10">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="text-sm text-gray-600">Loading...</span>
          </div>
        </div>
      )}
      
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

      <div className="space-y-6">
        {/* CSSEF Criteria Ratings */}
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">
            CSSEF Criteria (Rate 1-10)
          </h3>
          
          {CSSEF_CRITERIA.map((criterion) => (
            <div key={`criterion-${criterion.id}`} className="border border-gray-200 rounded-lg p-4">
              <div className="mb-3">
                <h4 className="font-medium text-gray-900 mb-1">{criterion.title}</h4>
                <p className="text-sm text-gray-600">{criterion.description}</p>
              </div>
              
              <div className="mb-3">
                <StarRating
                  rating={formData.ratings[criterion.id]?.score ?? null}
                  onRatingChange={(rating) => updateRating(criterion.id, 'score', rating)}
                />
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
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How confident are you in your self-assessment? *
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            {[1, 2, 3, 4, 5].map((level) => (
              <label key={level} className="flex items-center space-x-2 cursor-pointer p-2 rounded-md hover:bg-gray-50 transition-colors">
                <input
                  type="radio"
                  name="confidence_level"
                  value={level}
                  checked={formData.confidence_level === level}
                  onChange={(e) => updateConfidenceLevel(parseInt(e.target.value))}
                  className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500 focus:ring-2"
                />
                <span className="text-sm text-gray-700 leading-tight">
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