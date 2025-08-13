import axios from 'axios';

const API_URL = '/api/courses';

const getAllCourses = () => {
  return axios.get(API_URL);
};

const getCourseById = (id) => {
  return axios.get(`${API_URL}/${id}`);
};

const getLessonsByCourseId = (courseId) => {
  return axios.get(`${API_URL}/${courseId}/lessons`);
};

const courseService = {
  getAllCourses,
  getCourseById,
  getLessonsByCourseId,
};

export default courseService;
