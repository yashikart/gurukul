import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import GlassContainer from "../components/GlassContainer";
import { BookOpen, Brain, Clock, Award, Play } from "lucide-react";
import { useTranslation } from "react-i18next";

export default function Test() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [selectedSubject, setSelectedSubject] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("");

  // Sample subjects and topics for quiz generation
  const subjects = {
    "Mathematics": ["Algebra", "Geometry", "Calculus", "Statistics", "Trigonometry"],
    "Science": ["Physics", "Chemistry", "Biology", "Environmental Science"],
    "History": ["Ancient History", "Modern History", "World Wars", "Indian History"],
    "English": ["Grammar", "Literature", "Vocabulary", "Writing Skills"],
    "Computer Science": ["Programming", "Data Structures", "Algorithms", "Web Development"]
  };

  // Translated subject names for display
  const getTranslatedSubjectName = (subjectKey) => {
    const translations = {
      "Mathematics": t("Mathematics"),
      "Science": t("Science"),
      "History": t("History"),
      "English": t("English"),
      "Computer Science": t("Computer Science")
    };
    return translations[subjectKey] || subjectKey;
  };

  // Translated topic names for display
  const getTranslatedTopicName = (topicKey) => {
    const translations = {
      "Algebra": t("Algebra"),
      "Geometry": t("Geometry"),
      "Calculus": t("Calculus"),
      "Statistics": t("Statistics"),
      "Trigonometry": t("Trigonometry"),
      "Physics": t("Physics"),
      "Chemistry": t("Chemistry"),
      "Biology": t("Biology"),
      "Environmental Science": t("Environmental Science"),
      "Ancient History": t("Ancient History"),
      "Modern History": t("Modern History"),
      "World Wars": t("World Wars"),
      "Indian History": t("Indian History"),
      "Grammar": t("Grammar"),
      "Literature": t("Literature"),
      "Vocabulary": t("Vocabulary"),
      "Writing Skills": t("Writing Skills"),
      "Programming": t("Programming"),
      "Data Structures": t("Data Structures"),
      "Algorithms": t("Algorithms"),
      "Web Development": t("Web Development")
    };
    return translations[topicKey] || topicKey;
  };

  const handleStartQuiz = () => {
    if (selectedSubject && selectedTopic) {
      navigate(`/quiz/${selectedSubject}/${selectedTopic}`);
    }
  };

  return (
    <GlassContainer>
      <h2
        className="text-4xl md:text-5xl font-extrabold mb-6 drop-shadow-lg transition-all duration-300 hover:bg-gradient-to-r hover:from-white hover:to-[#FF9933] hover:bg-clip-text hover:text-transparent"
        style={{ color: "#FFFFFF", fontFamily: "Nunito, sans-serif" }}
      >
        {t("Test Center")}
      </h2>
      <p
        className="text-lg md:text-xl font-medium mb-8"
        style={{ color: "#FFFFFF", fontFamily: "Nunito, sans-serif" }}
      >
        {t("Take tests to evaluate your knowledge and track your progress.")}
      </p>

      {/* AI-Generated Quiz Section */}
      <div className="mb-12">
        <div className="bg-gradient-to-r from-orange-500/20 to-yellow-500/20 rounded-xl p-8 border border-orange-300/30 mb-8">
          <div className="flex items-center mb-6">
            <Brain className="w-8 h-8 text-orange-400 mr-3" />
            <h3 className="text-2xl font-bold text-white">{t("AI-Generated Quizzes")}</h3>
          </div>
          <p className="text-gray-300 mb-6">
            {t("Generate personalized quizzes based on your lesson content with intelligent questions and instant feedback.")}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-white font-medium mb-2">{t("Select Subject")}</label>
              <select
                value={selectedSubject}
                onChange={(e) => {
                  setSelectedSubject(e.target.value);
                  setSelectedTopic("");
                }}
                className="w-full p-3 rounded-lg bg-white/10 border border-gray-600 text-white focus:border-orange-500 focus:outline-none"
              >
                <option value="">{t("Choose a subject...")}</option>
                {Object.keys(subjects).map(subject => (
                  <option key={subject} value={subject} className="bg-gray-800">
                    {getTranslatedSubjectName(subject)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-white font-medium mb-2">{t("Select Topic")}</label>
              <select
                value={selectedTopic}
                onChange={(e) => setSelectedTopic(e.target.value)}
                disabled={!selectedSubject}
                className="w-full p-3 rounded-lg bg-white/10 border border-gray-600 text-white focus:border-orange-500 focus:outline-none disabled:opacity-50"
              >
                <option value="">{t("Choose a topic...")}</option>
                {selectedSubject && subjects[selectedSubject].map(topic => (
                  <option key={topic} value={topic} className="bg-gray-800">
                    {getTranslatedTopicName(topic)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6 text-sm text-gray-300">
              <div className="flex items-center">
                <Clock className="w-4 h-4 mr-2" />
                <span>{t("10-15 minutes")}</span>
              </div>
              <div className="flex items-center">
                <BookOpen className="w-4 h-4 mr-2" />
                <span>{t("5 questions")}</span>
              </div>
              <div className="flex items-center">
                <Award className="w-4 h-4 mr-2" />
                <span>{t("Instant feedback")}</span>
              </div>
            </div>

            <button
              onClick={handleStartQuiz}
              disabled={!selectedSubject || !selectedTopic}
              className="px-8 py-3 bg-gradient-to-r from-orange-500 to-yellow-500 text-white font-bold rounded-lg hover:from-orange-600 hover:to-yellow-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center shadow-lg"
            >
              <Play className="w-4 h-4 mr-2" />
              {t("Start Quiz")}
            </button>
          </div>
        </div>
      </div>
    </GlassContainer>
  );
}
