"use client";

import { useState } from "react";
import { toast } from "react-hot-toast";

// PRPSA Questions with their original text
const PRPSA_QUESTIONS = [
  { id: 1, text: "While preparing for giving a speech, I feel tense and nervous.", reverse: false },
  { id: 2, text: "I feel tense when I see the words \"speech\" and \"public speech\" on a course outline when studying.", reverse: false },
  { id: 3, text: "My thoughts become confused and jumbled when I am giving a speech.", reverse: false },
  { id: 4, text: "Right after giving a speech I feel that I have had a pleasant experience.", reverse: true },
  { id: 5, text: "I get anxious when I think about a speech coming up.", reverse: false },
  { id: 6, text: "I have no fear of giving a speech.", reverse: true },
  { id: 7, text: "Although I am nervous just before starting a speech, I soon settle down after starting and feel calm and comfortable.", reverse: true },
  { id: 8, text: "I look forward to giving a speech.", reverse: true },
  { id: 9, text: "When the instructor announces a speaking assignment in class, I can feel myself getting tense.", reverse: false },
  { id: 10, text: "My hands tremble when I am giving a speech.", reverse: false },
  { id: 11, text: "I feel relaxed while giving a speech.", reverse: true },
  { id: 12, text: "I enjoy preparing for a speech.", reverse: true },
  { id: 13, text: "I am in constant fear of forgetting what I prepared to say.", reverse: false },
  { id: 14, text: "I get anxious if someone asks me something about my topic that I don't know.", reverse: false },
  { id: 15, text: "I face the prospect of giving a speech with confidence.", reverse: true },
  { id: 16, text: "I feel that I am in complete possession of myself while giving a speech.", reverse: true },
  { id: 17, text: "My mind is clear when giving a speech.", reverse: true },
  { id: 18, text: "I do not dread giving a speech.", reverse: true },
  { id: 19, text: "I perspire just before starting a speech.", reverse: false },
  { id: 20, text: "My heart beats very fast just as I start a speech.", reverse: false },
  { id: 21, text: "I experience considerable anxiety while sitting in the room just before my speech starts.", reverse: false },
  { id: 22, text: "Certain parts of my body feel very tense and rigid while giving a speech.", reverse: false },
  { id: 23, text: "Realizing that only a little time remains in a speech makes me very tense and anxious.", reverse: false },
  { id: 24, text: "While giving a speech, I know I can control my feelings of tension and stress.", reverse: true },
  { id: 25, text: "I breathe faster just before starting a speech.", reverse: false },
  { id: 26, text: "I feel comfortable and relaxed in the hour or so just before giving a speech.", reverse: true },
  { id: 27, text: "I do poorer on speeches because I am anxious.", reverse: false },
  { id: 28, text: "I feel anxious when the teacher announces the date of a speaking assignment.", reverse: false },
  { id: 29, text: "When I make a mistake while giving a speech, I find it hard to concentrate on the parts that follow.", reverse: false },
  { id: 30, text: "During an important speech I experience a feeling of helplessness building up inside me.", reverse: false },
  { id: 31, text: "I have trouble falling asleep the night before a speech.", reverse: false },
  { id: 32, text: "My heart beats very fast while I present a speech.", reverse: false },
  { id: 33, text: "I feel anxious while waiting to give my speech.", reverse: false },
  { id: 34, text: "While giving a speech, I get so nervous I forget facts I really know.", reverse: false }
];

const LIKERT_SCALE = [
  { value: 1, label: "Strongly Disagree" },
  { value: 2, label: "Disagree" },
  { value: 3, label: "Neutral" },
  { value: 4, label: "Agree" },
  { value: 5, label: "Strongly Agree" }
];

interface UserPRPSAAssessmentProps {
  assessmentType: 'initial' | 'post_experimental';
  onComplete: (assessment: any) => void;
  onCancel: () => void;
  existingResponses?: Record<string, number>;
  isUpdate?: boolean;
}

export default function UserPRPSAAssessment({ 
  assessmentType,
  onComplete, 
  onCancel, 
  existingResponses = {}, 
  isUpdate = false 
}: UserPRPSAAssessmentProps) {
  const [responses, setResponses] = useState<Record<string, number>>(existingResponses);
  const [currentPage, setCurrentPage] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  const questionsPerPage = 5;
  const totalPages = Math.ceil(PRPSA_QUESTIONS.length / questionsPerPage);
  const currentQuestions = PRPSA_QUESTIONS.slice(
    currentPage * questionsPerPage,
    (currentPage + 1) * questionsPerPage
  );

  const handleResponseChange = (questionId: number, value: number) => {
    setResponses(prev => ({
      ...prev,
      [`q${questionId}`]: value
    }));
  };

  const getCompletedCount = () => {
    return Object.keys(responses).length;
  };

  const isCurrentPageComplete = () => {
    return currentQuestions.every(q => responses[`q${q.id}`] !== undefined);
  };

  const canSubmit = () => {
    return getCompletedCount() === 34;
  };

  const handleNext = () => {
    if (currentPage < totalPages - 1) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevious = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleSubmit = async () => {
    if (!canSubmit()) {
      toast.error("Please answer all questions before submitting");
      return;
    }

    setSubmitting(true);
    try {
      // Import the API utility dynamically to avoid SSR issues
      const { userPRPSAApi } = await import('../lib/api');
      
      let data;
      if (isUpdate) {
        data = await userPRPSAApi.updateAssessment(assessmentType, responses);
      } else {
        data = await userPRPSAApi.submitAssessment(assessmentType, responses);
      }
      
      toast.success(data.message);
      onComplete(data.assessment);
    } catch (error) {
      console.error("Error submitting user PRPSA:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to submit assessment";
      toast.error(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const getProgressPercentage = () => {
    return Math.round((getCompletedCount() / 34) * 100);
  };

  const getAssessmentTitle = () => {
    return assessmentType === 'initial' 
      ? 'Initial Public Speaking Anxiety Assessment'
      : 'Post-Experimental Public Speaking Anxiety Assessment';
  };

  const getAssessmentDescription = () => {
    return assessmentType === 'initial'
      ? 'This initial assessment will help us understand your current feelings about public speaking. Your responses will be used to track your progress throughout your journey with the speech coach.'
      : 'This post-experimental assessment will help us measure any changes in your public speaking anxiety after using the speech coach. Please answer honestly based on how you feel now.';
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          {getAssessmentTitle()}
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          {getAssessmentDescription()}
        </p>
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Personal Report of Public Speaking Anxiety (PRPSA)</strong><br />
            This assessment measures your feelings about public speaking. Please respond honestly to each statement 
            based on how you typically feel. There are no right or wrong answers.
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            Progress: {getCompletedCount()}/34 questions completed
          </span>
          <span className="text-sm text-gray-500">
            Page {currentPage + 1} of {totalPages}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${getProgressPercentage()}%` }}
          ></div>
        </div>
      </div>

      {/* Questions */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <div className="space-y-6">
          {currentQuestions.map((question, index) => (
            <div key={question.id} className="border-b border-gray-100 pb-6 last:border-b-0">
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Question {question.id}
                </h3>
                <p className="text-gray-700">
                  {question.text}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {LIKERT_SCALE.map((option) => (
                  <label
                    key={option.value}
                    className={`flex flex-col items-center p-3 border-2 rounded-lg cursor-pointer transition-colors ${
                      responses[`q${question.id}`] === option.value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      value={option.value}
                      checked={responses[`q${question.id}`] === option.value}
                      onChange={() => handleResponseChange(question.id, option.value)}
                      className="sr-only"
                    />
                    <span className="text-sm font-medium text-gray-900 mb-1">
                      {option.value}
                    </span>
                    <span className="text-xs text-gray-600 text-center">
                      {option.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between items-center">
        <div className="flex space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          {currentPage > 0 && (
            <button
              onClick={handlePrevious}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Previous
            </button>
          )}
        </div>

        <div className="text-sm text-gray-500">
          {!isCurrentPageComplete() && currentPage < totalPages - 1 && (
            <span>Answer all questions on this page to continue</span>
          )}
        </div>

        <div className="flex space-x-3">
          {currentPage < totalPages - 1 ? (
            <button
              onClick={handleNext}
              disabled={!isCurrentPageComplete()}
              className={`px-4 py-2 rounded-md font-medium transition-colors ${
                isCurrentPageComplete()
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!canSubmit() || submitting}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                canSubmit() && !submitting
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {submitting ? 'Submitting...' : isUpdate ? 'Update Assessment' : 'Submit Assessment'}
            </button>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Instructions:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Read each statement carefully and select the response that best describes your feelings</li>
          <li>• Use the 1-5 scale where 1 = Strongly Disagree and 5 = Strongly Agree</li>
          <li>• Answer based on your typical feelings, not just recent experiences</li>
          <li>• Be honest - this assessment is confidential and for your benefit</li>
          {assessmentType === 'post_experimental' && (
            <li>• Compare your current feelings to how you felt before using the speech coach</li>
          )}
        </ul>
      </div>
    </div>
  );
}