import React from 'react'
import styles from './ErrorBoundary.module.css'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Sonar Sentry UI Error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className={styles.errorBox}>
          <h3 className={styles.title}>Application Interface Warning</h3>
          <p>An unexpected display error occurred while rendering the sonar interface.</p>
          <div className={styles.message}>
            {this.state.error?.message || String(this.state.error)}
          </div>
          <button
            type="button"
            className={styles.retryBtn}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Retry View
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
