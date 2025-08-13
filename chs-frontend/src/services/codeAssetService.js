import axios from 'axios';

const API_URL = '/api/assets';

const getAllCodeSnippets = () => {
  return axios.get(`${API_URL}/snippets`);
};

const getCodeSnippetById = (id) => {
  return axios.get(`${API_URL}/snippets/${id}`);
};

const getAllNotebooks = () => {
  return axios.get(`${API_URL}/notebooks`);
};

const getNotebookById = (id) => {
  return axios.get(`${API_URL}/notebooks/${id}`);
};

const codeAssetService = {
  getAllCodeSnippets,
  getCodeSnippetById,
  getAllNotebooks,
  getNotebookById,
};

export default codeAssetService;
