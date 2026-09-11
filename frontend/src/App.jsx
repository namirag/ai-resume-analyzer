import { useState } from "react";
import axios from "axios";

function App() {
  const [resume, setResume] = useState(null);
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [message, setMessage] = useState("");
  const [analysis, setAnalysis] = useState(null);

  const handleAnalyze = async () => {
    if (!resume || !jobTitle || !jobDescription) {
      setMessage("Please provide a resume, job title, and job description.");
      return;
    }

    try {
      setAnalysis(null);
      setMessage("Uploading resume...");

      const formData = new FormData();
      formData.append("file", resume);

      const resumeResponse = await axios.post(
        "http://localhost:8000/resume/upload",
        formData
      );

      const resumeId = resumeResponse.data.id;

      setMessage("Saving job description...");

      const jobResponse = await axios.post(
        "http://localhost:8000/job",
        {
          title: jobTitle,
          description: jobDescription,
        }
      );

      const jobId = jobResponse.data.id;

      setMessage("Analyzing resume with AI...");

      const analysisResponse = await axios.get(
        `http://localhost:8000/match/${resumeId}/${jobId}`
      );

      console.log("Analysis:", analysisResponse.data);

      setAnalysis(analysisResponse.data.analysis);
      setMessage("Analysis completed successfully!");
    } catch (error) {
      console.error(error);
      setMessage("Something went wrong. Please check the backend.");
    }
  };

  return (
    <div className="container">

      <div className="header">
        <h1>AI Resume Analyzer</h1>
        <p>
          Analyze your resume against a job description using AI.
        </p>
      </div>

      <div className="card">
        <h2>Resume & Job Analysis</h2>

        <div className="form-group">
          <label>Resume</label>
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(event) => setResume(event.target.files[0])}
          />
        </div>

        <div className="form-group">
          <label>Job Title</label>
          <input
            type="text"
            placeholder="e.g. Data Scientist"
            value={jobTitle}
            onChange={(event) => setJobTitle(event.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Job Description</label>
          <textarea
            rows="12"
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
          />
        </div>

        <button onClick={handleAnalyze}>
          Analyze Resume
        </button>

        {message && <p className="message">{message}</p>}
      </div>

      {analysis && (
        <div className="card">
          <h2>Analysis Results</h2>

          <h3>Match Score</h3>
          <p>{analysis.match_score}%</p>

          <h3>Matching Skills</h3>
          <ul>
            {analysis.matching_skills.map((skill, index) => (
              <li key={index}>{skill}</li>
            ))}
          </ul>

          <h3>Missing Skills</h3>
          <ul>
            {analysis.missing_skills.map((skill, index) => (
              <li key={index}>{skill}</li>
            ))}
          </ul>

          <h3>Strengths</h3>
          <ul>
            {analysis.strengths.map((strength, index) => (
              <li key={index}>{strength}</li>
            ))}
          </ul>

          <h3>Recommendations</h3>
          <ul>
            {analysis.recommendations.map((recommendation, index) => (
              <li key={index}>{recommendation}</li>
            ))}
          </ul>

          <h3>Interview Questions</h3>
          <ul>
            {analysis.interview_questions.map((question, index) => (
              <li key={index}>{question}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;