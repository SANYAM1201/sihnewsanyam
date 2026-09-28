import { useRef } from 'react'
import styles from './UploadPanel.module.css'

const ACCEPT = '.tif,.tiff,.png,.jpg,.jpeg,.geotiff,.xtf,image/tiff,image/png,image/jpeg,application/octet-stream,application/x-xtf'

export default function UploadPanel({ file, previewUrl, onFile }) {
  const inputRef = useRef(null)

  function takeFile(next) {
    if (!next) return
    onFile(next)
  }

  function onDrop(event) {
    event.preventDefault()
    takeFile(event.dataTransfer.files?.[0])
  }

  const isXtf = file?.name?.toLowerCase().endsWith('.xtf')

  return (
    <section className={styles.panel}>
      <div>
        <div className={styles.panelTitle}>SONAR IMAGE UPLOAD SECTION</div>
        <div className={styles.panelSub}>.tiff · .geotiff · .png · .jpg · .xtf — up to 500MB</div>
      </div>
      <label
        className={styles.dropzone}
        tabIndex={0}
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
      >
        {isXtf ? (
          <div className={styles.xtfCard}>
            <span className={styles.xtfBadge}>XTF</span>
            <div className={styles.xtfDetails}>
              <strong className={styles.xtfTitle}>{file.name}</strong>
              <span className={styles.xtfSub}>Triton Side-Scan Sonar Telemetry & Waterfall Stream</span>
            </div>
          </div>
        ) : previewUrl ? (
          <div className={styles.thumbWrap}>
            <img src={previewUrl} alt={file?.name || 'Uploaded sonar image preview'} />
          </div>
        ) : null}
        <div className={styles.icon}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="24" height="24">
            <path d="M12 13v8m-8-6.101A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" />
            <path d="m8 17l4-4l4 4" />
          </svg>
        </div>
        <h2 className={styles.headline}>{file ? file.name : 'Drop sonar file here'}</h2>
        <span className={styles.meta}>
          {file
            ? `${(file.size / (1024 * 1024)).toFixed(2)} MB · ready to configure`
            : 'Upload the sonar images in respected formats · upto 60 MB'}
        </span>
        <div className={styles.formats}>
          <span className={styles.chip}>TIFF</span>
          <span className={styles.chip}>GEOTIFF</span>
          <span className={styles.chip}>PNG</span>
          <span className={styles.chip}>JPG</span>
          <span className={styles.chip}>XTF</span>
        </div>
        <div className={styles.fileActions}>
          <button
            className={styles.btnBrowse}
            type="button"
            onClick={(e) => {
              e.preventDefault()
              inputRef.current?.click()
            }}
          >
            Browse files
          </button>
          <button
            className={styles.btnDemoScan}
            type="button"
            title="Instantly generate an authentic 450 kHz dual-channel side-scan sonar swath"
            onClick={async (e) => {
              e.preventDefault()
              e.stopPropagation()
              try {
                const { createDemoSonarFile } = await import('../../utils/generateDemoSonar')
                const { sonarAudio } = await import('../../utils/sonarAudio')
                sonarAudio.playPing(1100, 0.4)
                const demoFile = await createDemoSonarFile()
                takeFile(demoFile)
              } catch (err) {
                console.error('Failed to load demo swath:', err)
              }
            }}
          >
            <span style={{ fontSize: '15px' }}>⚡</span>
            <span>Load Demo Sonar Scan</span>
            <span className={styles.demoTag}>450 kHz</span>
          </button>
          {file ? (
            <button
              className={styles.btnRemove}
              type="button"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                onFile(null)
                if (inputRef.current) inputRef.current.value = ''
              }}
            >
              Remove file
            </button>
          ) : null}
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          hidden
          onChange={(e) => takeFile(e.target.files?.[0])}
        />
      </label>
    </section>
  )
}
