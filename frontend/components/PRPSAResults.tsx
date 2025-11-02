"use client";

interface PRPSAResult {
  id: number;
  speech_id: number;
  total_score: number;
  anxiety_level: string;
  completed_at: string;
  responses?: Record<string, number>;
}

interface PRPSAResultsProps {
  prpsa: PRPSAResult;
  showResponses?: boolean;
}

export default function PRPSAResults({ prpsa, showResponses = false }: PRPSAResultsProps) {
  const getAnxietyLevelColor = (level: string) => {
    switch (level) {
      case 'Low':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'Moderate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'High':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getAnxietyDescription = (level: string, score: number) => {
    switch (level) {
      case 'Low':
        return {
          title: 'Low Public Speaking Anxiety',
          description: 'You experience minimal anxiety when speaking in public. You likely feel comfortable and confident in most speaking situations.',
          tips: [
            'Continue practicing to maintain your confidence',
            'Consider helping others who struggle with speaking anxiety',
            'Challenge yourself with more complex speaking opportunities'
          ]
        };
      case 'Moderate':
        return {
          title: 'Moderate Public Speaking Anxiety',
          description: 'You experience some anxiety when speaking in public, which is normal and manageable. With practice and preparation, you can continue to improve.',
          tips: [
            'Focus on thorough preparation and practice',
            'Use relaxation techniques before speaking',
            'Gradually increase your speaking opportunities',
            'Consider joining speaking groups like Toastmasters'
          ]
        };
      case 'High':
        return {
          title: 'High Public Speaking Anxiety',
          description: 'You experience significant anxiety when speaking in public. This is common and can be improved with dedicated practice and techniques.',
          tips: [
            'Start with smaller, low-stakes speaking opportunities',
            'Practice deep breathing and relaxation techniques',
            'Work on building confidence through preparation',
            'Consider seeking support from speaking coaches or counselors',
            'Focus on gradual exposure to speaking situations'
          ]
        };
      default:
        return {
          title: 'Unknown Anxiety Level',
          description: 'Unable to determine anxiety level.',
          tips: []
        };
    }
  };

  const anxietyInfo = getAnxietyDescription(prpsa.anxiety_level, prpsa.total_score);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          PRPSA Assessment Results
        </h2>
        <p className="text-gray-600">
          Completed on {formatDate(prpsa.completed_at)}
        </p>
      </div>

      {/* Score Overview */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="grid md:grid-cols-2 gap-6">
          {/* Score */}
          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900 mb-2">
              {prpsa.total_score}
            </div>
            <div className="text-sm text-gray-600 mb-4">
              PRPSA Score (Range: 34-170)
            </div>
            <div className={`inline-block px-4 py-2 rounded-full border font-medium ${getAnxietyLevelColor(prpsa.anxiety_level)}`}>
              {prpsa.anxiety_level} Anxiety
            </div>
          </div>

          {/* Score Range Visualization */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Score Interpretation</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Low (34-97)</span>
                <span>Moderate (98-131)</span>
                <span>High (132-170)</span>
              </div>
              <div className="relative h-4 bg-gradient-to-r from-green-200 via-yellow-200 to-red-200 rounded">
                <div
                  className="absolute top-0 w-2 h-4 bg-gray-800 rounded"
                  style={{
                    left: `${((prpsa.total_score - 34) / (170 - 34)) * 100}%`,
                    transform: 'translateX(-50%)'
                  }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Results */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {anxietyInfo.title}
        </h3>
        <p className="text-gray-700 mb-4">
          {anxietyInfo.description}
        </p>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-3">Recommendations for Improvement:</h4>
          <ul className="space-y-2">
            {anxietyInfo.tips.map((tip, index) => (
              <li key={index} className="flex items-start text-sm text-blue-800">
                <span className="text-blue-600 mr-2 mt-1">•</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Understanding Your Score
        </h3>
        <div className="grid md:grid-cols-3 gap-4 text-center">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-800 mb-1">34-97</div>
            <div className="text-sm font-medium text-green-700 mb-2">Low Anxiety</div>
            <div className="text-xs text-green-600">
              Comfortable with public speaking
            </div>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-800 mb-1">98-131</div>
            <div className="text-sm font-medium text-yellow-700 mb-2">Moderate Anxiety</div>
            <div className="text-xs text-yellow-600">
              Normal level, manageable with practice
            </div>
          </div>
          
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-800 mb-1">132-170</div>
            <div className="text-sm font-medium text-red-700 mb-2">High Anxiety</div>
            <div className="text-xs text-red-600">
              Focus on techniques and gradual exposure
            </div>
          </div>
        </div>
      </div>

      {/* Research Information */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          About the PRPSA Assessment
        </h3>
        <div className="text-sm text-gray-700 space-y-2">
          <p>
            The Personal Report of Public Speaking Anxiety (PRPSA) is a research-validated instrument 
            developed by James McCroskey to measure public speaking anxiety levels.
          </p>
          <p>
            <strong>Mean Score:</strong> 114.6 | <strong>Standard Deviation:</strong> 17.2
          </p>
          <p className="text-xs text-gray-600 mt-4">
            Reference: McCroskey, J. C. (1970). Measures of communication-bound anxiety. Speech Monographs, 37, 269-277.
          </p>
        </div>
      </div>
    </div>
  );
}