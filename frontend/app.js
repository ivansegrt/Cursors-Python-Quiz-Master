// Determine API base URL with flexible overrides
// Priority: window.API_BASE_URL > ?api= query param > localStorage > default
(() => {
  try {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get('api');
    if (fromQuery) {
      // Persist selection for subsequent loads
      localStorage.setItem('API_BASE_URL', fromQuery);
      window.API_BASE_URL = fromQuery;
    }
  } catch (_) {
    // ignore URL parsing/localStorage errors
  }
})();

const pageOrigin = (typeof window !== 'undefined' && window.location && window.location.origin)
  ? window.location.origin
  : null;

const safeOrigin = (pageOrigin && pageOrigin !== 'null' && !pageOrigin.startsWith('file'))
  ? pageOrigin
  : null;

const API_BASE_URL = window.API_BASE_URL
  || (typeof localStorage !== 'undefined' ? localStorage.getItem('API_BASE_URL') : null)
  || safeOrigin
  || 'http://localhost:8000';
const OPTION_KEYS = ['a', 'b', 'c', 'd'];

const elements = {
	totalQuestions: document.getElementById('total-questions'),
	score: document.getElementById('score'),
	lastResult: document.getElementById('last-result'),
	questionNumber: document.getElementById('question-number'),
	questionText: document.getElementById('question-text'),
	options: document.getElementById('options'),
	feedback: document.getElementById('feedback'),
	submitBtn: document.getElementById('submit-btn'),
	skipBtn: document.getElementById('skip-btn'),
	nextBtn: document.getElementById('next-btn'),
	toast: document.getElementById('toast'),
};

const state = {
	currentQuestion: null,
	selectedAnswer: null,
	score: {
		correct: 0,
		total: 0,
	},
	isLoading: false,
	isSubmitting: false,
};

async function fetchJson(url, options = {}) {
	const response = await fetch(url, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...(options.headers || {}),
		},
	});

	if (!response.ok) {
		const message = await extractErrorMessage(response);
		throw new Error(message);
	}

	return response.json();
}

async function extractErrorMessage(response) {
	try {
		const data = await response.json();
		if (data?.detail) {
			if (Array.isArray(data.detail)) {
				return data.detail.map((item) => item.msg || item).join(', ');
			}
			return data.detail;
		}
		if (data?.message) {
			return data.message;
		}
		return `Request failed with status ${response.status}`;
	} catch (error) {
		return `Request failed with status ${response.status}`;
	}
}

function showToast(message, timeout = 3000) {
	if (!elements.toast) return;
	elements.toast.textContent = message;
	elements.toast.classList.add('visible');

	setTimeout(() => {
		elements.toast.classList.remove('visible');
	}, timeout);
}

function updateScoreDisplay() {
	const { correct, total } = state.score;
	elements.score.textContent = `${correct} / ${total}`;
}

function setLastResult(message, isCorrect = null) {
	elements.lastResult.textContent = message;
	if (isCorrect === true) {
		elements.lastResult.style.color = '#bbf7d0';
	} else if (isCorrect === false) {
		elements.lastResult.style.color = '#fecaca';
	} else {
		elements.lastResult.style.color = 'rgba(226, 232, 240, 0.65)';
	}
}

function resetFeedback() {
	elements.feedback.textContent = '';
	elements.feedback.className = 'feedback';
	elements.feedback.classList.remove('visible');
}

function clearOptions() {
	elements.options.innerHTML = '';
	state.selectedAnswer = null;
	elements.submitBtn.disabled = true;
}

function renderQuestion(question) {
	state.currentQuestion = question;
	state.selectedAnswer = null;
	elements.questionNumber.textContent = `Question #${question.id + 1}`;
	elements.questionText.textContent = question.question_text;

	clearOptions();
	resetFeedback();

	question.options.forEach((optionText, index) => {
		const optionKey = OPTION_KEYS[index];
		const li = document.createElement('li');
		li.className = 'option';
		li.dataset.optionKey = optionKey;

		const labelSpan = document.createElement('span');
		labelSpan.className = 'option-label';
		labelSpan.textContent = optionKey.toUpperCase();

		const textSpan = document.createElement('span');
		textSpan.className = 'option-text';
		textSpan.textContent = optionText;

		li.appendChild(labelSpan);
		li.appendChild(textSpan);

		li.addEventListener('click', () => onOptionSelected(optionKey));

		elements.options.appendChild(li);
	});

	elements.submitBtn.disabled = true;
	elements.submitBtn.classList.remove('hidden');
	elements.skipBtn.disabled = false;
	elements.skipBtn.classList.remove('hidden');
	elements.nextBtn.classList.add('hidden');
}

function onOptionSelected(optionKey) {
	if (state.isSubmitting) {
		return;
	}

	state.selectedAnswer = optionKey;
	[...elements.options.children].forEach((li) => {
		if (li.dataset.optionKey === optionKey) {
			li.classList.add('selected');
		} else {
			li.classList.remove('selected');
		}
	});
	elements.submitBtn.disabled = false;
}

function highlightAnswers(correctKey, submittedKey) {
	[...elements.options.children].forEach((li) => {
		const key = li.dataset.optionKey;
		if (key === correctKey) {
			li.classList.add('correct');
		}
		if (submittedKey && key === submittedKey && submittedKey !== correctKey) {
			li.classList.add('incorrect');
		}
		li.classList.remove('selected');
	});
}

async function fetchStats() {
	try {
		const { total_questions: totalQuestions } = await fetchJson(`${API_BASE_URL}/api/stats`);
		elements.totalQuestions.textContent = totalQuestions;
	} catch (error) {
		console.error(error);
		showToast(`Stats error: ${error.message}`);
		elements.totalQuestions.textContent = 'N/A';
	}
}

async function fetchRandomQuestion({ showLoader = true } = {}) {
	if (state.isLoading) return;
	state.isLoading = true;

	try {
		if (showLoader) {
			elements.questionText.textContent = 'Fetching question...';
			clearOptions();
		}

		const question = await fetchJson(`${API_BASE_URL}/api/questions/random`);
		renderQuestion(question);
	} catch (error) {
		console.error(error);
		showToast(`Unable to get question: ${error.message}`);
		elements.questionText.textContent = 'Unable to load question. Please try again.';
	} finally {
		state.isLoading = false;
	}
}

async function submitCurrentAnswer() {
	if (!state.currentQuestion || !state.selectedAnswer) {
		showToast('Please select an answer before submitting.');
		return;
	}
	if (state.isSubmitting) return;

	state.isSubmitting = true;
	elements.submitBtn.disabled = true;
	elements.skipBtn.disabled = true;

	try {
		const payload = {
			question_id: state.currentQuestion.id,
			answer: state.selectedAnswer,
		};

		const result = await fetchJson(`${API_BASE_URL}/api/quiz/submit`, {
			method: 'POST',
			body: JSON.stringify(payload),
		});

		state.score.total += 1;
		if (result.is_correct) {
			state.score.correct += 1;
		}
		updateScoreDisplay();

		const correctKey = result.correct_answer;
		highlightAnswers(correctKey, state.selectedAnswer);

		elements.feedback.textContent = `${result.is_correct ? 'Great job! 🎉' : 'Not quite. 🤔'} ${result.explanation}`;
		elements.feedback.classList.add('visible');
		elements.feedback.classList.toggle('correct', result.is_correct);
		elements.feedback.classList.toggle('incorrect', !result.is_correct);

		setLastResult(result.is_correct ? 'Correct' : 'Incorrect', result.is_correct);

		elements.nextBtn.classList.remove('hidden');
		elements.skipBtn.classList.add('hidden');
	} catch (error) {
		console.error(error);
		showToast(`Submit failed: ${error.message}`);
		elements.submitBtn.disabled = false;
		elements.skipBtn.disabled = false;
	} finally {
		state.isSubmitting = false;
	}
}

function setupEventListeners() {
	elements.submitBtn.addEventListener('click', submitCurrentAnswer);
	elements.skipBtn.addEventListener('click', () => {
		setLastResult('Skipped', null);
		resetFeedback();
		fetchRandomQuestion({ showLoader: false });
	});
	elements.nextBtn.addEventListener('click', () => {
		resetFeedback();
		setLastResult('-', null);
		fetchRandomQuestion({ showLoader: false });
	});
}

async function initialize() {
	updateScoreDisplay();
	setLastResult('-', null);
	setupEventListeners();
	await fetchStats();
	await fetchRandomQuestion();
}

document.addEventListener('DOMContentLoaded', initialize);

