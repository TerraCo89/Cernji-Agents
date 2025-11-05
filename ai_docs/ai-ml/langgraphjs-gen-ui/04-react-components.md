# React Component Patterns

## Component Structure

### Basic Component

```tsx
// ui/WeatherCard.tsx
interface WeatherCardProps {
  city: string;
  temperature: number;
  conditions: string;
}

export default function WeatherCard({ city, temperature, conditions }: WeatherCardProps) {
  return (
    <div className="weather-card">
      <h3>{city}</h3>
      <div className="temperature">{temperature}°F</div>
      <div className="conditions">{conditions}</div>
    </div>
  );
}
```

### Component with useStreamContext

```tsx
import { useStreamContext } from "@langchain/langgraph-sdk/react-ui";

interface WeatherCardProps {
  city: string;
  temperature: number;
}

export default function WeatherCard({ city, temperature }: WeatherCardProps) {
  const { submit, thread } = useStreamContext();

  const handleRefresh = () => {
    submit({
      messages: [{
        type: "human",
        content: `Refresh weather for ${city}`
      }]
    });
  };

  return (
    <div className="weather-card">
      <h3>{city}</h3>
      <div className="temperature">{temperature}°F</div>
      <button onClick={handleRefresh}>Refresh</button>
    </div>
  );
}
```

## Common Patterns

### 1. Image Display

```tsx
interface ImageViewerProps {
  image_data: string;
  media_type: string;
  caption?: string;
}

export default function ImageViewer({ image_data, media_type, caption }: ImageViewerProps) {
  const [isLoading, setIsLoading] = useState(true);

  return (
    <div className="image-viewer">
      {isLoading && <div className="skeleton-loader" />}
      <img
        src={`data:${media_type};base64,${image_data}`}
        alt={caption || "Image"}
        onLoad={() => setIsLoading(false)}
        loading="lazy"
      />
      {caption && <p className="caption">{caption}</p>}
    </div>
  );
}
```

### 2. Gallery Component

```tsx
interface GalleryProps {
  images: Array<{
    id: string;
    data: string;
    media_type: string;
    caption?: string;
  }>;
}

export default function Gallery({ images }: GalleryProps) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  return (
    <>
      <div className="gallery-grid">
        {images.map((image) => (
          <div
            key={image.id}
            className="gallery-item"
            onClick={() => setSelectedImage(image.id)}
          >
            <img
              src={`data:${image.media_type};base64,${image.data}`}
              alt={image.caption || ""}
              loading="lazy"
            />
          </div>
        ))}
      </div>

      {selectedImage && (
        <Modal onClose={() => setSelectedImage(null)}>
          <img
            src={`data:${images.find(i => i.id === selectedImage)?.media_type};base64,${
              images.find(i => i.id === selectedImage)?.data
            }`}
            alt="Full size"
          />
        </Modal>
      )}
    </>
  );
}
```

### 3. Flashcard Component

```tsx
interface Card {
  id: string;
  front: string;
  back: string;
}

interface FlashcardProps {
  cards: Card[];
}

export default function Flashcard({ cards }: FlashcardProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const { submit } = useStreamContext();

  const handleFlip = () => setIsFlipped(!isFlipped);

  const handleNext = () => {
    if (currentIndex < cards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsFlipped(false);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setIsFlipped(false);
    }
  };

  const handleRate = (difficulty: 'easy' | 'medium' | 'hard') => {
    submit({
      messages: [{
        type: "human",
        content: JSON.stringify({
          action: "rate_card",
          cardId: cards[currentIndex].id,
          difficulty
        })
      }]
    });
    handleNext();
  };

  return (
    <div className="flashcard-container">
      <div className="progress">
        {currentIndex + 1} / {cards.length}
      </div>

      <div
        className={`flip-card ${isFlipped ? 'flipped' : ''}`}
        onClick={handleFlip}
      >
        <div className="flip-card-inner">
          <div className="flip-card-front">
            {cards[currentIndex].front}
          </div>
          <div className="flip-card-back">
            {cards[currentIndex].back}
          </div>
        </div>
      </div>

      {isFlipped && (
        <div className="rating-buttons">
          <button onClick={() => handleRate('easy')}>Easy</button>
          <button onClick={() => handleRate('medium')}>Medium</button>
          <button onClick={() => handleRate('hard')}>Hard</button>
        </div>
      )}

      <div className="navigation">
        <button onClick={handlePrevious} disabled={currentIndex === 0}>
          Previous
        </button>
        <button onClick={handleNext} disabled={currentIndex === cards.length - 1}>
          Next
        </button>
      </div>
    </div>
  );
}
```

### 4. Data Table

```tsx
interface DataTableProps {
  columns: string[];
  rows: Array<Record<string, any>>;
  sortable?: boolean;
}

export default function DataTable({ columns, rows, sortable = true }: DataTableProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const handleSort = (column: string) => {
    if (!sortable) return;

    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const sortedRows = sortColumn
    ? [...rows].sort((a, b) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];
        const multiplier = sortDirection === 'asc' ? 1 : -1;
        return aVal > bVal ? multiplier : -multiplier;
      })
    : rows;

  return (
    <div className="data-table">
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col} onClick={() => handleSort(col)}>
                {col}
                {sortColumn === col && (
                  <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td key={col}>{row[col]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### 5. Chart Component (with Recharts)

```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

interface ChartProps {
  data: Array<Record<string, number>>;
  xKey: string;
  yKeys: string[];
  title?: string;
}

export default function Chart({ data, xKey, yKeys, title }: ChartProps) {
  const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c'];

  return (
    <div className="chart-container">
      {title && <h3>{title}</h3>}
      <LineChart width={600} height={300} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} />
        <YAxis />
        <Tooltip />
        <Legend />
        {yKeys.map((key, idx) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={colors[idx % colors.length]}
          />
        ))}
      </LineChart>
    </div>
  );
}
```

### 6. Progressive Content (Streaming)

```tsx
interface WriterProps {
  content: string;
}

export default function Writer({ content }: WriterProps) {
  const isStreaming = content.length > 0 && !content.endsWith('.');

  return (
    <div className="writer-panel">
      <div className="content">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
      {isStreaming && (
        <div className="streaming-indicator">
          <span className="cursor-blink">▊</span>
        </div>
      )}
    </div>
  );
}
```

### 7. Form Component

```tsx
interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'email' | 'select';
  options?: string[];
  required?: boolean;
}

interface FormProps {
  fields: FormField[];
  submitLabel?: string;
}

export default function Form({ fields, submitLabel = "Submit" }: FormProps) {
  const { submit } = useStreamContext();
  const [formData, setFormData] = useState<Record<string, any>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    submit({
      messages: [{
        type: "human",
        content: JSON.stringify({
          action: "form_submit",
          data: formData
        })
      }]
    });
  };

  return (
    <form onSubmit={handleSubmit} className="dynamic-form">
      {fields.map((field) => (
        <div key={field.name} className="form-field">
          <label>
            {field.label}
            {field.required && <span className="required">*</span>}
          </label>

          {field.type === 'select' ? (
            <select
              value={formData[field.name] || ''}
              onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
              required={field.required}
            >
              <option value="">Select...</option>
              {field.options?.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          ) : (
            <input
              type={field.type}
              value={formData[field.name] || ''}
              onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
              required={field.required}
            />
          )}
        </div>
      ))}

      <button type="submit">{submitLabel}</button>
    </form>
  );
}
```

### 8. Error Component

```tsx
interface ErrorCardProps {
  error_type: string;
  error_message: string;
  retry_action?: string;
}

export default function ErrorCard({ error_type, error_message, retry_action }: ErrorCardProps) {
  const { submit } = useStreamContext();

  const handleRetry = () => {
    if (retry_action) {
      submit({
        messages: [{
          type: "human",
          content: JSON.stringify({
            action: "retry",
            retry_action
          })
        }]
      });
    }
  };

  return (
    <div className="error-card">
      <div className="error-icon">⚠️</div>
      <div className="error-content">
        <h3>{error_type}</h3>
        <p>{error_message}</p>
      </div>
      {retry_action && (
        <button onClick={handleRetry}>Retry</button>
      )}
    </div>
  );
}
```

## Component Registration

### Export Map

```tsx
// ui/components.tsx
import WeatherCard from './WeatherCard';
import ImageViewer from './ImageViewer';
import Gallery from './Gallery';
import Flashcard from './Flashcard';
import DataTable from './DataTable';
import Chart from './Chart';
import Writer from './Writer';
import Form from './Form';
import ErrorCard from './ErrorCard';

// Export component map
export default {
  weather_card: WeatherCard,
  image_viewer: ImageViewer,
  gallery: Gallery,
  flashcard: Flashcard,
  data_table: DataTable,
  chart: Chart,
  writer: Writer,
  form: Form,
  error_card: ErrorCard,
};

// For type safety
export type ComponentMap = typeof default;
```

## Styling Patterns

### CSS Modules

```css
/* WeatherCard.module.css */
.weatherCard {
  border-radius: 12px;
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.temperature {
  font-size: 2.5rem;
  font-weight: bold;
  margin: 0.5rem 0;
}

.conditions {
  font-size: 1rem;
  opacity: 0.9;
}
```

```tsx
import styles from './WeatherCard.module.css';

export default function WeatherCard({ city, temperature, conditions }) {
  return (
    <div className={styles.weatherCard}>
      <h3>{city}</h3>
      <div className={styles.temperature}>{temperature}°F</div>
      <div className={styles.conditions}>{conditions}</div>
    </div>
  );
}
```

### Tailwind CSS

```tsx
export default function WeatherCard({ city, temperature, conditions }) {
  return (
    <div className="rounded-xl p-6 bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg">
      <h3 className="text-xl font-semibold mb-2">{city}</h3>
      <div className="text-4xl font-bold my-4">{temperature}°F</div>
      <div className="text-sm opacity-90">{conditions}</div>
    </div>
  );
}
```

## Best Practices

### 1. Type Safety

```tsx
// Define props interface
interface ComponentProps {
  required: string;
  optional?: number;
}

// Use TypeScript for validation
export default function Component({ required, optional = 0 }: ComponentProps) {
  // TypeScript ensures props are correct
}
```

### 2. Error Boundaries

```tsx
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error }) {
  return (
    <div className="error-fallback">
      <h2>Something went wrong</h2>
      <pre>{error.message}</pre>
    </div>
  );
}

// Wrap components in error boundary
<ErrorBoundary FallbackComponent={ErrorFallback}>
  <MyComponent />
</ErrorBoundary>
```

### 3. Loading States

```tsx
export default function ImageViewer({ image_data, media_type }) {
  const [isLoading, setIsLoading] = useState(true);

  return (
    <>
      {isLoading && <Skeleton />}
      <img
        src={`data:${media_type};base64,${image_data}`}
        onLoad={() => setIsLoading(false)}
        style={{ display: isLoading ? 'none' : 'block' }}
      />
    </>
  );
}
```

### 4. Memoization

```tsx
import { memo, useMemo } from 'react';

export default memo(function ExpensiveComponent({ data }) {
  const processedData = useMemo(() => {
    return data.map(item => expensiveOperation(item));
  }, [data]);

  return <div>{/* render processedData */}</div>;
});
```

### 5. Accessibility

```tsx
export default function Flashcard({ cards }) {
  return (
    <div
      className="flashcard"
      role="button"
      tabIndex={0}
      aria-label={`Flashcard ${currentIndex + 1} of ${cards.length}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleFlip();
        }
      }}
    >
      {/* content */}
    </div>
  );
}
```

## Testing

### Component Tests

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import WeatherCard from './WeatherCard';

describe('WeatherCard', () => {
  it('displays weather information', () => {
    render(
      <WeatherCard
        city="San Francisco"
        temperature={72}
        conditions="Sunny"
      />
    );

    expect(screen.getByText('San Francisco')).toBeInTheDocument();
    expect(screen.getByText('72°F')).toBeInTheDocument();
    expect(screen.getByText('Sunny')).toBeInTheDocument();
  });

  it('calls refresh on button click', () => {
    const mockSubmit = jest.fn();
    jest.mock('@langchain/langgraph-sdk/react-ui', () => ({
      useStreamContext: () => ({ submit: mockSubmit })
    }));

    render(<WeatherCard city="NYC" temperature={65} conditions="Cloudy" />);

    fireEvent.click(screen.getByText('Refresh'));
    expect(mockSubmit).toHaveBeenCalled();
  });
});
```

## Next Steps

- **[05-integration-guide.md](05-integration-guide.md)**: Integrate components into apps
- **[06-examples.md](06-examples.md)**: Complete working examples
