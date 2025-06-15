import React, { useState } from 'react';
import { apiClient, GenerationRequest } from '../api/client';

interface BookGenerationFormProps {
  onGenerationStart?: (request: GenerationRequest) => void;
  onGenerationComplete?: () => void;
  onError?: (error: string) => void;
}

export const BookGenerationForm: React.FC<BookGenerationFormProps> = ({
  onGenerationStart,
  onGenerationComplete,
  onError
}) => {
  const [formData, setFormData] = useState<GenerationRequest>({
    topic: '',
    target_audience: 'beginners',
    style: 'professional',
    pages: 100,
    language: 'en'
  });
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!formData.topic.trim()) {
      errors.topic = 'Topic is required';
    } else if (formData.topic.length < 10) {
      errors.topic = 'Topic should be at least 10 characters long';
    }
    
    if (formData.pages && (formData.pages < 10 || formData.pages > 1000)) {
      errors.pages = 'Pages should be between 10 and 1000';
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsGenerating(true);
    setValidationErrors({});
    
    try {
      onGenerationStart?.(formData);
      const response = await apiClient.generateBook(formData);
      console.log('Generation started:', response);
      onGenerationComplete?.();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start book generation';
      console.error('Generation error:', error);
      onError?.(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleInputChange = (field: keyof GenerationRequest, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear validation error when user starts typing
    if (validationErrors[field]) {
      setValidationErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Generate New Book</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Topic Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Book Topic *
          </label>
          <textarea
            value={formData.topic}
            onChange={(e) => handleInputChange('topic', e.target.value)}
            placeholder="Enter a detailed topic for your book (e.g., 'Advanced Machine Learning Techniques for Natural Language Processing')"
            className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              validationErrors.topic ? 'border-red-500' : 'border-gray-300'
            }`}
            rows={3}
            disabled={isGenerating}
          />
          {validationErrors.topic && (
            <p className="mt-1 text-sm text-red-600">{validationErrors.topic}</p>
          )}
        </div>

        {/* Form Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Target Audience */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Audience
            </label>
            <select
              value={formData.target_audience}
              onChange={(e) => handleInputChange('target_audience', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isGenerating}
            >
              <option value="beginners">Beginners</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="professionals">Professionals</option>
              <option value="students">Students</option>
              <option value="researchers">Researchers</option>
            </select>
          </div>

          {/* Writing Style */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Writing Style
            </label>
            <select
              value={formData.style}
              onChange={(e) => handleInputChange('style', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isGenerating}
            >
              <option value="professional">Professional</option>
              <option value="academic">Academic</option>
              <option value="conversational">Conversational</option>
              <option value="technical">Technical</option>
              <option value="authoritative">Authoritative</option>
              <option value="narrative">Narrative</option>
            </select>
          </div>

          {/* Page Count */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Pages
            </label>
            <input
              type="number"
              value={formData.pages}
              onChange={(e) => handleInputChange('pages', parseInt(e.target.value) || 100)}
              min={10}
              max={1000}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                validationErrors.pages ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={isGenerating}
            />
            {validationErrors.pages && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.pages}</p>
            )}
          </div>

          {/* Language */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Language
            </label>
            <select
              value={formData.language}
              onChange={(e) => handleInputChange('language', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isGenerating}
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="it">Italian</option>
              <option value="pt">Portuguese</option>
            </select>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isGenerating}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              isGenerating
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
            } text-white`}
          >
            {isGenerating ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Generating Book...</span>
              </div>
            ) : (
              'Start Generation'
            )}
          </button>
        </div>
      </form>

      {/* Generation Info */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-sm font-medium text-gray-700 mb-2">What happens next?</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• AI agents will analyze your topic and create a detailed outline</li>
          <li>• Content will be generated chapter by chapter with quality checks</li>
          <li>• Real-time progress updates will be shown in the dashboard</li>
          <li>• The final book will be available for download in multiple formats</li>
        </ul>
      </div>
    </div>
  );
};

export default BookGenerationForm;