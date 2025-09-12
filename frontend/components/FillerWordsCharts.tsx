import { Bar } from 'react-chartjs-2';
import { Chart, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
Chart.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);


type FillerWordsObject = {
  fillers: Record<string, number>;
  total: number;
};

type FillerWordsChartProps = {
  fillerWords: FillerWordsObject;
};

const getFillerChartData = (fillersObj: FillerWordsObject | undefined) => {
  if (!fillersObj || !fillersObj.fillers) return null;
  const labels = Object.keys(fillersObj.fillers);
  const data = Object.values(fillersObj.fillers);
  return {
    labels,
    datasets: [
      {
        label: 'Filler Words',
        data,
        backgroundColor: 'rgba(30, 64, 175, 0.7)',
      },
    ],
  };
};

const FillerWordsChart: React.FC<FillerWordsChartProps> = ({ fillerWords }) => {
  return <Bar
    data={getFillerChartData(fillerWords)!}
    options={{
      responsive: true,
      plugins: {
        legend: { display: false },
        title: { display: true, text: 'Filler Words Frequency' },
      },
    }}
  />;
};

export default FillerWordsChart;
