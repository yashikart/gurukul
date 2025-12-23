import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import GlassContainer from '../components/GlassContainer';
import CenteredLoader from '../components/CenteredLoader';
import { CheckCircle, XCircle, Clock, Award, BookOpen, ArrowLeft, ArrowRight } from 'lucide-react';
import { useSelector } from 'react-redux';
import { selectUser } from '../store/authSlice';
import { processTestResult, dispatchKarmaChange } from '../utils/karmaManager';
import { toast } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';

const QuizPage = () => {
  const { subject, topic } = useParams();
  const navigate = useNavigate();
  const user = useSelector(selectUser);
  const { t, i18n } = useTranslation();
  
  const [quiz, setQuiz] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState(null);
  const [timeLeft, setTimeLeft] = useState(null);
  const [error, setError] = useState(null);

  // Generate quiz on component mount
  useEffect(() => {
    generateQuiz();
  }, [subject, topic]);

  // Timer effect
  useEffect(() => {
    if (timeLeft > 0 && !results) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0 && !results) {
      handleSubmitQuiz();
    }
  }, [timeLeft, results]);

  const generateQuiz = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Get current language (map i18n language to backend format; handle ar-* locales)
      const currentLanguage =
        i18n.language && i18n.language.toLowerCase().startsWith("ar")
          ? "arabic"
          : "english";
      
      const response = await fetch('http://localhost:8005/quiz/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subject: subject || 'General Knowledge',
          topic: topic || 'Mixed Topics',
          num_questions: 10,
          difficulty: 'medium',
          question_types: ['multiple_choice', 'true_false'],
          language: currentLanguage
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate quiz');
      }

      const data = await response.json();
      setQuiz(data.quiz);
      setTimeLeft(data.quiz.estimated_time * 60); // Convert minutes to seconds
      
    } catch (error) {
      console.error('Error generating quiz:', error);
      setError('Failed to generate quiz. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnswerSelect = (questionId, answer) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!quiz) return;
    
    try {
      setIsSubmitting(true);
      
      // Determine language for submission (match backend expectations)
      const currentLanguage =
        i18n.language && i18n.language.toLowerCase().startsWith("ar")
          ? "arabic"
          : "english";

      const response = await fetch('http://localhost:8005/quiz/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          quiz_id: quiz.quiz_id,
          user_answers: userAnswers,
          user_id: 'current_user',
          language: currentLanguage
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit quiz');
      }

      const data = await response.json();
      setResults(data.evaluation);
      
      // Process karma based on test result
      if (data.evaluation?.score_summary?.percentage_score !== undefined) {
        const effectiveUserId = user?.id || user?.user_id || 'guest-user';
        const percentageScore = data.evaluation.score_summary.percentage_score;
        const karmaResult = processTestResult(effectiveUserId, percentageScore);
        
        if (karmaResult) {
          dispatchKarmaChange(karmaResult);
          
          // Show toast notification
          if (karmaResult.change > 0) {
            toast.success(`+${karmaResult.change} Karma: ${karmaResult.reason}`, {
              position: "top-right",
              duration: 3000,
            });
          } else {
            toast.error(`${karmaResult.change} Karma: ${karmaResult.reason}`, {
              position: "top-right",
              duration: 3000,
            });
          }
        }
      }
      
    } catch (error) {
      console.error('Error submitting quiz:', error);
      setError('Failed to submit quiz. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getGradeColor = (grade) => {
    switch (grade) {
      case 'A': return 'text-green-400';
      case 'B': return 'text-blue-400';
      case 'C': return 'text-yellow-400';
      case 'D': return 'text-orange-400';
      default: return 'text-red-400';
    }
  };

  if (isLoading) {
    return (
      <GlassContainer>
        <div className="relative" style={{ height: "calc(100vh - 350px)" }}>
          <CenteredLoader />
          <p className="text-center text-white mt-4">{t("Generating your quiz...")}</p>
        </div>
      </GlassContainer>
    );
  }

  if (error) {
    return (
      <GlassContainer>
        <div className="text-center">
          <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-4">{t("Error")}</h2>
          <p className="text-red-400 mb-6">{error}</p>
          <button
            onClick={() => navigate('/subjects')}
            className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
          >
            {t("Back to Subjects")}
          </button>
        </div>
      </GlassContainer>
    );
  }

  if (results) {
    return (
      <GlassContainer>
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <Award className="w-20 h-20 text-yellow-400 mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-white mb-2">{t("Quiz Complete!")}</h2>
            <p className="text-gray-300">{t("Here are your results")}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white/10 rounded-lg p-6 text-center">
              <h3 className="text-lg font-semibold text-white mb-2">{t("Score")}</h3>
              <p className="text-3xl font-bold text-orange-400">
                {results.score_summary.percentage_score}%
              </p>
            </div>
            <div className="bg-white/10 rounded-lg p-6 text-center">
              <h3 className="text-lg font-semibold text-white mb-2">{t("Grade")}</h3>
              <p className={`text-3xl font-bold ${getGradeColor(results.score_summary.grade)}`}>
                {results.score_summary.grade}
              </p>
            </div>
            <div className="bg-white/10 rounded-lg p-6 text-center">
              <h3 className="text-lg font-semibold text-white mb-2">{t("Correct")}</h3>
              <p className="text-3xl font-bold text-green-400">
                {results.score_summary.correct_answers}/{results.score_summary.total_questions}
              </p>
            </div>
          </div>

          <div className="bg-white/10 rounded-lg p-6 mb-6">
            <h3 className="text-xl font-bold text-white mb-4">{t("Performance Analysis")}</h3>
            <p className="text-gray-300 mb-4">
              {t("Overall Performance")}: <span className="text-orange-400 font-semibold">
                {results.performance_analysis.overall_performance}
              </span>
            </p>
            
            {results.performance_analysis.recommendations.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold text-white mb-2">{t("Recommendations")}:</h4>
                <ul className="list-disc list-inside text-gray-300 space-y-1">
                  {results.performance_analysis.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="flex justify-center space-x-4">
            <button
              onClick={() => navigate('/subjects')}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors flex items-center"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              {t("Back to Subjects")}
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
              {t("Take Another Quiz")}
            </button>
          </div>
        </div>
      </GlassContainer>
    );
  }

  if (!quiz) {
    return (
      <GlassContainer>
        <div className="text-center">
          <p className="text-white">{t("No quiz available")}</p>
        </div>
      </GlassContainer>
    );
  }

  const currentQ = quiz.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100;

  return (
    <GlassContainer>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">{quiz.subject} - {quiz.topic}</h1>
            <p className="text-gray-300">{t("Question")} {currentQuestion + 1} {t("of")} {quiz.questions.length}</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center text-white">
              <Clock className="w-4 h-4 mr-2" />
              {timeLeft !== null && formatTime(timeLeft)}
            </div>
            <div className="flex items-center text-white">
              <BookOpen className="w-4 h-4 mr-2" />
              {quiz.difficulty}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-700 rounded-full h-2 mb-8">
          <div 
            className="bg-orange-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>

        {/* Question */}
        <div className="bg-white/10 rounded-lg p-8 mb-6">
          <h2 className="text-xl font-semibold text-white mb-6">{currentQ.question}</h2>
          
          {currentQ.type === 'multiple_choice' && (
            <div className="space-y-3">
              {currentQ.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleAnswerSelect(currentQ.question_id, index)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    userAnswers[currentQ.question_id] === index
                      ? 'border-orange-500 bg-orange-500/20 text-white'
                      : 'border-gray-600 bg-white/5 text-gray-300 hover:border-gray-500 hover:bg-white/10'
                  }`}
                >
                  <span className="font-medium mr-3">{String.fromCharCode(65 + index)}.</span>
                  {option}
                </button>
              ))}
            </div>
          )}

          {currentQ.type === 'true_false' && (
            <div className="space-y-3">
              {[true, false].map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleAnswerSelect(currentQ.question_id, option)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    userAnswers[currentQ.question_id] === option
                      ? 'border-orange-500 bg-orange-500/20 text-white'
                      : 'border-gray-600 bg-white/5 text-gray-300 hover:border-gray-500 hover:bg-white/10'
                  }`}
                >
                  {option ? t('True') : t('False')}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
            disabled={currentQuestion === 0}
            className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t("Previous")}
          </button>

          {currentQuestion === quiz.questions.length - 1 ? (
            <button
              onClick={handleSubmitQuiz}
              disabled={isSubmitting || Object.keys(userAnswers).length !== quiz.questions.length}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {t("Submitting...")}
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  {t("Submit Quiz")}
                </>
              )}
            </button>
          ) : (
            <button
              onClick={() => setCurrentQuestion(Math.min(quiz.questions.length - 1, currentQuestion + 1))}
              disabled={currentQuestion === quiz.questions.length - 1}
              className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {t("Next")}
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          )}
        </div>
      </div>
    </GlassContainer>
  );
};

export default QuizPage;
