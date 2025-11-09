"use client";

import { useState } from "react";
import { withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import UserPRPSAAssessment from "../../../components/UserPRPSAAssessment";
import UserPRPSAResults from "../../../components/UserPRPSAResults";

type ViewState = 'results' | 'initial_assessment' | 'post_experimental_assessment';

function AssessmentsPage() {
  const [currentView, setCurrentView] = useState<ViewState>('results');

  const handleTakeAssessment = (type: 'initial' | 'post_experimental') => {
    setCurrentView(type === 'initial' ? 'initial_assessment' : 'post_experimental_assessment');
  };

  const handleAssessmentComplete = (assessment: any) => {
    console.log('Assessment completed:', assessment);
    setCurrentView('results');
  };

  const handleCancel = () => {
    setCurrentView('results');
  };

  if (currentView === 'initial_assessment') {
    return (
      <UserPRPSAAssessment
        assessmentType="initial"
        onComplete={handleAssessmentComplete}
        onCancel={handleCancel}
      />
    );
  }

  if (currentView === 'post_experimental_assessment') {
    return (
      <UserPRPSAAssessment
        assessmentType="post_experimental"
        onComplete={handleAssessmentComplete}
        onCancel={handleCancel}
      />
    );
  }

  return (
    <UserPRPSAResults 
      onTakeAssessment={handleTakeAssessment}
    />
  );
}

export default withPageAuthRequired(AssessmentsPage);