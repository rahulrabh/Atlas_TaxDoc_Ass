import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = "http://localhost:8000";

function App() {
  const [taxCases, setTaxCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [reviewDocument, setReviewDocument] = useState(null);

  const [status, setStatus] = useState(null);
  const [reviews, setReviews] = useState([]);

  const [showAddCase, setShowAddCase] = useState(false);
  const [file, setFile] = useState(null);

  useEffect(() => {
    loadTaxCases();
  }, []);

  async function loadTaxCases() {
    try {
      const response = await axios.get(
        `${API_BASE}/api/tax-cases/`
      );

      setTaxCases(response.data.tax_cases);
    } catch (error) {
      console.error(error);
    }
  }

  async function openCase(taxCase) {
    setSelectedCase(taxCase);
    setReviewDocument(null);

    try {
      const [statusResponse, reviewResponse] =
        await Promise.all([
          axios.get(
            `${API_BASE}/api/tax-cases/${taxCase.id}/collection-status/`
          ),
          axios.get(
            `${API_BASE}/api/tax-cases/${taxCase.id}/reviews/`
          ),
        ]);

      setStatus(statusResponse.data);
      setReviews(reviewResponse.data.reviews);
    } catch (error) {
      console.error(error);
      alert("Unable to load tax case.");
    }
  }

  async function uploadDocument() {
    if (!file || !selectedCase) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post(
        `${API_BASE}/api/tax-cases/${selectedCase.id}/documents/`,
        formData
      );

      setFile(null);

      await openCase(selectedCase);

      alert("Document uploaded successfully.");
    } catch (error) {
      console.error(error);
      alert("Upload failed.");
    }
  }

  function goToCases() {
    setSelectedCase(null);
    setReviewDocument(null);
    setStatus(null);
    setReviews([]);
  }

  function openReview(review) {
    setReviewDocument(review);
  }

  function closeReview() {
    setReviewDocument(null);
  }

  /*
   * LANDING PAGE
   */
  if (!selectedCase) {
    return (
      <div className="app">
        <header className="topbar">
          <div>
            <div className="brand">TaxDoc</div>
            <p className="subtitle">
              Tax document collection
            </p>
          </div>

          <button
            className="primary-button"
            onClick={() => setShowAddCase(true)}
          >
            + Add Tax Case
          </button>
        </header>

        <main>
          <div className="page-title">
            <h1>Tax Cases</h1>
            <p>
              Manage document collection across your
              clients.
            </p>
          </div>

          <div className="case-grid">
            {taxCases.map((taxCase) => (
              <div
                className="case-card"
                key={taxCase.id}
                onClick={() => openCase(taxCase)}
              >
                <div>
                  <span className="year">
                    {taxCase.tax_year}
                  </span>

                  <h2>
                    {taxCase.client_name}
                  </h2>

                  <p>
                    {taxCase.filing_status}
                  </p>
                </div>

                <div className="case-footer">
                  <span>
                    Open tax case
                  </span>

                  <span className="arrow">
                    →
                  </span>
                </div>
              </div>
            ))}
          </div>

          {taxCases.length === 0 && (
            <div className="empty-state">
              <h2>No tax cases yet</h2>
              <p>
                Create your first tax case to begin
                collecting documents.
              </p>

              <button
                className="primary-button"
                onClick={() => setShowAddCase(true)}
              >
                + Add Tax Case
              </button>
            </div>
          )}
        </main>

        {showAddCase && (
          <div className="modal-backdrop">
            <div className="modal">
              <div className="modal-header">
                <div>
                  <h2>Create Tax Case</h2>
                  <p>
                    Add a new client tax case.
                  </p>
                </div>

                <button
                  className="close-button"
                  onClick={() =>
                    setShowAddCase(false)
                  }
                >
                  ×
                </button>
              </div>

              <label>
                Client name
                <input
                  placeholder="Rahul Kumar"
                />
              </label>

              <label>
                Tax year
                <input
                  type="number"
                  placeholder="2025"
                />
              </label>

              <label>
                Filing status
                <select defaultValue="">
                  <option value="" disabled>
                    Select filing status
                  </option>
                  <option>
                    Single
                  </option>
                  <option>
                    Married Jointly
                  </option>
                  <option>
                    Married Separately
                  </option>
                  <option>
                    Head of Household
                  </option>
                </select>
              </label>

              <div className="modal-actions">
                <button
                  className="secondary-button"
                  onClick={() =>
                    setShowAddCase(false)
                  }
                >
                  Cancel
                </button>

                <button
                  className="primary-button"
                  disabled
                >
                  Create Case
                </button>
              </div>

              <p className="coming-soon">
                Case creation will be connected to
                the backend next.
              </p>
            </div>
          </div>
        )}
      </div>
    );
  }

  /*
   * REVIEW SCREEN
   */
  if (reviewDocument) {
    return (
      <div className="app">
        <header className="topbar">
          <div>
            <div className="brand">TaxDoc</div>
          </div>
        </header>

        <main>
          <button
            className="back-button"
            onClick={closeReview}
          >
            ← Back to case
          </button>

          <div className="page-title review-title">
            <span className="eyebrow">
              DOCUMENT REVIEW
            </span>

            <h1>
              Review document
            </h1>

            <p>
              Confirm the classification before
              matching it to a requirement.
            </p>
          </div>

          <div className="review-layout">
            <section className="card document-preview">
              <div className="document-icon">
                PDF
              </div>

              <h2>
                {reviewDocument.file_name}
              </h2>

              <p>
                Current classification:
              </p>

              <span className="review-badge">
                REVIEW REQUIRED
              </span>
            </section>

            <section className="card">
              <h2>Confirm classification</h2>

              <label>
                Document type
                <select defaultValue="">
                  <option value="" disabled>
                    Select document type
                  </option>
                  <option>W2</option>
                  <option>FORM_1040</option>
                  <option>1099_INT</option>
                  <option>1099_DIV</option>
                </select>
              </label>

              <label>
                Tax year
                <input
                  type="number"
                  placeholder="2025"
                />
              </label>

              <div className="info-box">
                The confirmed classification will
                be matched against the tax case
                requirements.
              </div>

              <button
                className="primary-button full-width"
                disabled
              >
                Confirm Classification
              </button>

              <p className="coming-soon">
                Resolution will be connected to
                the backend next.
              </p>
            </section>
          </div>
        </main>
      </div>
    );
  }

  /*
   * CASE DASHBOARD
   */
  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="brand">TaxDoc</div>
        </div>

        <button
          className="secondary-button"
          onClick={goToCases}
        >
          ← All Tax Cases
        </button>
      </header>

      <main>
        <div className="page-title">
          <span className="eyebrow">
            TAX CASE
          </span>

          <h1>
            {selectedCase.client_name}
          </h1>

          <p>
            {selectedCase.tax_year} ·{" "}
            {selectedCase.filing_status}
          </p>
        </div>

        {status && (
          <section className="summary">
            <div className="summary-card">
              <span>Total</span>
              <strong>
                {status.summary.total}
              </strong>
            </div>

            <div className="summary-card">
              <span>Received</span>
              <strong>
                {status.summary.received}
              </strong>
            </div>

            <div className="summary-card">
              <span>Outstanding</span>
              <strong>
                {status.summary.outstanding}
              </strong>
            </div>

            <div className="summary-card">
              <span>Needs Review</span>
              <strong>
                {status.summary.needs_review}
              </strong>
            </div>
          </section>
        )}

        <div className="dashboard-grid">
          <section className="card">
            <div className="section-header">
              <div>
                <h2>Document requirements</h2>
                <p>
                  Track the documents needed for
                  this tax return.
                </p>
              </div>
            </div>

            {status?.requirements.map(
              (requirement) => (
                <div
                  className="requirement"
                  key={
                    requirement.requirement_id
                  }
                >
                  <div>
                    <strong>
                      {
                        requirement.document_type
                      }
                    </strong>

                    <span>
                      {requirement.tax_year}
                    </span>
                  </div>

                  <span
                    className={`badge ${
                      requirement.status ===
                      "RECEIVED"
                        ? "received"
                        : "outstanding"
                    }`}
                  >
                    {requirement.status}
                  </span>
                </div>
              )
            )}
          </section>

          <section className="card">
            <div className="section-header">
              <h2>Upload document</h2>

              <p>
                Upload a document for automatic
                classification.
              </p>
            </div>

            <input
              type="file"
              onChange={(event) =>
                setFile(
                  event.target.files[0]
                )
              }
            />

            <button
              className="primary-button upload-button"
              onClick={uploadDocument}
              disabled={!file}
            >
              Upload Document
            </button>
          </section>
        </div>

        <section className="card">
          <div className="section-header">
            <h2>Needs review</h2>

            <p>
              Documents where the system needs
              accountant confirmation.
            </p>
          </div>

          {reviews.length === 0 ? (
            <div className="empty-inline">
              ✓ No documents need review.
            </div>
          ) : (
            reviews.map((review) => (
              <div
                className="review"
                key={review.document_id}
              >
                <div>
                  <strong>
                    {review.file_name}
                  </strong>

                  <span>
                    Confidence:{" "}
                    {review.confidence}
                  </span>
                </div>

                <button
                  className="secondary-button"
                  onClick={() =>
                    openReview(review)
                  }
                >
                  Review →
                </button>
              </div>
            ))
          )}
        </section>
      </main>
    </div>
  );
}

export default App;