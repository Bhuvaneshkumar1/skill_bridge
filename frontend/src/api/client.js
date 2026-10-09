// REST API Client helper for backend connection

const BASE_URL = '/api';

async function fetchJSON(endpoint, options = {}) {
  const savedStudentId = typeof window !== 'undefined' ? localStorage.getItem('skillbridge_student_id') : null;
  const customHeaders = { ...options.headers };
  if (savedStudentId && !customHeaders['X-Student-Id'] && !customHeaders['Authorization']) {
    customHeaders['X-Student-Id'] = savedStudentId;
  }

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...customHeaders,
    },
    ...options,
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network request failed' }));
    const msg = typeof errorData.detail === 'string'
      ? errorData.detail
      : (Array.isArray(errorData.detail)
          ? errorData.detail.map(e => e.msg || e.detail || JSON.stringify(e)).join(', ')
          : (errorData.detail ? JSON.stringify(errorData.detail) : `Request failed with status ${response.status}`));
    throw new Error(msg);
  }

  return response.json();
}

export const api = {
  // Profiles
  createProfile: (data) => fetchJSON('/profiles', { method: 'POST', body: JSON.stringify(data) }),
  getProfile: (id) => fetchJSON(`/profiles/${id}`),
  updateProfile: (id, data) => fetchJSON(`/profiles/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  listProfiles: () => fetchJSON('/profiles'),

  // Careers & Skill Gap
  listCareers: () => fetchJSON('/careers'),
  getCareerMap: (careerName) => fetchJSON(`/careers/${encodeURIComponent(careerName)}`),
  getSkillGap: (careerName, studentId, forceRefresh = false) => {
    const q = forceRefresh ? '?force_refresh=true' : '';
    return fetchJSON(`/careers/${encodeURIComponent(careerName)}/gap-analysis/${studentId}${q}`);
  },

  // Resources
  searchResources: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return fetchJSON(`/resources?${query}`);
  },

  // Plans
  generatePlan: (studentId, planDays = 7) => fetchJSON('/plans/generate', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId, plan_days: planDays })
  }),
  getPlan: (studentId) => fetchJSON(`/plans/${studentId}`),
  toggleTask: (taskId) => fetchJSON(`/plans/task/${taskId}/toggle-complete`, { method: 'POST' }),

  // Teaching & Agent
  teachConcept: (studentId, topic, preferredMethod) => fetchJSON('/teaching/teach', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId, topic, preferred_method: preferredMethod })
  }),
  adaptMethod: (studentId, topic, score, currentMethod, struggledAspects = []) => fetchJSON('/teaching/adapt', {
    method: 'POST',
    body: JSON.stringify({
      student_id: studentId,
      topic,
      assessment_score: score,
      current_method: currentMethod,
      struggled_aspects: struggledAspects
    })
  }),
  chatWithAgent: (studentId, message) => fetchJSON('/teaching/chat', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId, message })
  }),

  // Quiz & Eval
  getQuizStatus: (topic) => fetchJSON(`/quiz/status/${encodeURIComponent(topic)}`),
  completeModule: (studentId, topic, moduleName = 'concept_explanation') => fetchJSON('/quiz/complete-module', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId, topic, module_name: moduleName })
  }),
  generateQuiz: (studentId, topic, numQuestions = 5) => fetchJSON('/quiz/generate', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId, topic, num_questions: numQuestions })
  }),
  submitQuiz: (studentId, quizId, topic, answers) => fetchJSON('/quiz/submit', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId, quiz_id: quizId, topic, answers })
  }),
  evaluateQuiz: (studentId, quizId, topic, answers) => fetchJSON('/quiz/submit', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId, quiz_id: quizId, topic, answers })
  }),

  // Progress
  getProgress: (studentId) => fetchJSON(`/progress/${studentId}`),

  // Sandbox API
  runSandboxCode: (data) => fetchJSON('/sandbox/run', { method: 'POST', body: JSON.stringify(data) }),
  submitSandboxCode: (data) => fetchJSON('/sandbox/submit', { method: 'POST', body: JSON.stringify(data) })
};

