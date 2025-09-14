import { useState, useEffect, useRef } from 'react';
import { Card, Heading, Text, Box, Flex, Badge } from '@radix-ui/themes';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const API_BASE = 'http://localhost:8000';

export function EEGVisualization({ isStudying = false, currentCard = null, studyStats = { total_cards_studied: 0 } }) {
  const [eegData, setEegData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [isLoading, setIsLoading] = useState(true);
  const chartRef = useRef(null);
  const startTimeRef = useRef(null);

  useEffect(() => {
    let eegIntervalId;
    
    if (isStudying) {
      // Poll for EEG data every 500ms when studying
      eegIntervalId = setInterval(fetchEEGData, 500);
      fetchEEGData(); // Initial fetch
    } else {
      // Single fetch when not studying
      fetchEEGData();
    }

    return () => {
      if (eegIntervalId) clearInterval(eegIntervalId);
    };
  }, [isStudying]);

  const fetchEEGData = async () => {
    try {
      // Fetch both status and raw EEG data
      const [statusResponse, dataResponse] = await Promise.all([
        fetch(`${API_BASE}/eeg/status`),
        fetch(`${API_BASE}/eeg/data?seconds=5.0`)
      ]);

      const status = await statusResponse.json();
      const rawData = await dataResponse.json();

      setConnectionStatus(status.connection_quality || 'disconnected');
      setEegData(rawData.data && rawData.data.length > 0 ? rawData.data : null);
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching EEG data:', error);
      setConnectionStatus('error');
      setIsLoading(false);
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'excellent': return 'green';
      case 'good': return 'blue';
      case 'fair': return 'orange';
      case 'poor': return 'yellow';
      case 'disconnected': return 'gray';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'excellent': return 'Excellent Signal';
      case 'good': return 'Good Signal';
      case 'fair': return 'Fair Signal';
      case 'poor': return 'Poor Signal';
      case 'disconnected': return 'Not Connected';
      case 'error': return 'Connection Error';
      default: return 'Unknown';
    }
  };

  const getLastStudiedTime = () => {
    if (!currentCard || !currentCard.last_reviewed) {
      return 'Never';
    }
    
    try {
      const lastReviewed = new Date(currentCard.last_reviewed);
      const now = new Date();
      const diffMs = now - lastReviewed;
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      
      if (diffMinutes < 1) return 'Just now';
      if (diffMinutes < 60) return `${diffMinutes}m`;
      if (diffHours < 24) return `${diffHours}h`;
      return `${diffDays}d`;
    } catch (error) {
      return 'Unknown';
    }
  };

  // Prepare data for Chart.js
  const prepareChartData = () => {
    if (!eegData || eegData.length === 0) {
      return null;
    }

    // Initialize start time on first data
    if (startTimeRef.current === null && eegData.length > 0) {
      startTimeRef.current = eegData[0].timestamp;
    }

    // Create time labels (relative to the very first timestamp we saw)
    const timeLabels = eegData.map(d => ((d.timestamp - startTimeRef.current)).toFixed(2));
    
    // Channel colors
    const colors = {
      tp9: '#FF6B6B',    // Red
      af7: '#4ECDC4',    // Teal  
      af8: '#45B7D1',    // Blue
      tp10: '#96CEB4'    // Green
    };

    return {
      labels: timeLabels,
      datasets: [
        {
          label: 'TP9 (μV)',
          data: eegData.map(d => d.tp9),
          borderColor: colors.tp9,
          backgroundColor: colors.tp9 + '20',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.1,
        },
        {
          label: 'AF7 (μV)',
          data: eegData.map(d => d.af7),
          borderColor: colors.af7,
          backgroundColor: colors.af7 + '20',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.1,
        },
        {
          label: 'AF8 (μV)',
          data: eegData.map(d => d.af8),
          borderColor: colors.af8,
          backgroundColor: colors.af8 + '20',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.1,
        },
        {
          label: 'TP10 (μV)',
          data: eegData.map(d => d.tp10),
          borderColor: colors.tp10,
          backgroundColor: colors.tp10 + '20',
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 4,
          tension: 0.1,
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 0, // Disable animations for real-time updates
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          pointStyle: 'line',
          font: {
            size: 12,
          },
          generateLabels: (chart) => {
            const datasets = chart.data.datasets;
            return datasets.map((dataset, i) => ({
              text: dataset.label,
              fillStyle: dataset.borderColor,
              strokeStyle: dataset.borderColor,
              lineWidth: 2,
              pointStyle: 'line',
              datasetIndex: i,
            }));
          },
        },
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Time (seconds)',
          font: {
            size: 12,
            weight: 'bold',
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
          lineWidth: 1,
        },
        ticks: {
          maxTicksLimit: 10,
          font: {
            size: 10,
          },
        },
      },
      y: {
        display: true,
        min: 400,
        max: 1000,
        title: {
          display: true,
          text: 'Amplitude (μV)',
          font: {
            size: 12,
            weight: 'bold',
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
          lineWidth: 1,
        },
        ticks: {
          font: {
            size: 10,
          },
          stepSize: 100,
        },
      },
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false,
    },
    elements: {
      line: {
        borderJoinStyle: 'round',
      },
    },
  };

  const chartData = prepareChartData();

  return (
    <Card size="3">
        <Flex direction="column" gap="3">
          <Flex justify="between" align="center">
            <Heading size="4">Study Session Monitor</Heading>
            <Badge color={getConnectionStatusColor()} variant="soft">
              {getConnectionStatusText()}
            </Badge>
          </Flex>

          {/* Main split layout */}
          <Flex gap="4" style={{ height: 200 }}>
            {/* Left Half - Info Boxes */}
            <Flex direction="column" gap="2" style={{ flex: 1 }}>
              {/* Top Box - Cognitive Load */}
              <Card size="2" style={{ height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Flex align="center" gap="2">
                  <Text size="2" color="gray">Cognitive Load:</Text>
                  <Badge color="orange" variant="soft" size="2">
                    Medium
                  </Badge>
                </Flex>
              </Card>

              {/* Bottom Boxes - Stats */}
              <Flex gap="2" style={{ height: '110px' }}>
                <Card size="2" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Flex direction="column" gap="1" align="center">
                    <Text size="4" weight="bold" color="blue">{studyStats?.total_cards_studied || 0}</Text>
                    <Text size="1" color="gray">cards today</Text>
                  </Flex>
                </Card>
                
                <Card size="2" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Flex direction="column" gap="1" align="center">
                    <Text size="4" weight="bold" color="green">{getLastStudiedTime()}</Text>
                    <Text size="1" color="gray">ago</Text>
                  </Flex>
                </Card>
              </Flex>
            </Flex>

            {/* Right Half - EEG Visualization */}
            <Box style={{ flex: 1 }}>
              <Card size="2" style={{ height: '100%' }}>
                <Flex direction="column" gap="1" style={{ height: '100%' }}>
                  <Flex align="center" justify="center" style={{ minHeight: '30px' }}>
                    <Text size="2" color="gray" weight="medium">Live EEG Signal</Text>
                  </Flex>
                  
                  {isLoading ? (
                    <Box style={{ 
                      height: '160px',
                      backgroundColor: 'var(--gray-3)', 
                      borderRadius: 'var(--radius-2)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Text size="2" color="gray">Loading EEG data...</Text>
                    </Box>
                  ) : connectionStatus === 'disconnected' ? (
                    <Box style={{ 
                      height: '160px',
                      backgroundColor: 'var(--gray-3)', 
                      borderRadius: 'var(--radius-2)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '8px'
                    }}>
                      <Text size="2" color="gray">No EEG device connected</Text>
                      <Text size="1" color="gray" style={{ textAlign: 'center' }}>
                        Connect your Muse headband
                      </Text>
                    </Box>
                  ) : !chartData ? (
                    <Box style={{ 
                      height: '160px',
                      backgroundColor: 'var(--gray-3)', 
                      borderRadius: 'var(--radius-2)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Text size="2" color="gray">Waiting for EEG data...</Text>
                    </Box>
                  ) : (
                    <Box style={{ 
                      height: '160px',
                      position: 'relative',
                      backgroundColor: 'white',
                      borderRadius: 'var(--radius-2)',
                      border: '1px solid var(--gray-6)',
                      padding: '8px'
                    }}>
                      <Line 
                        ref={chartRef}
                        data={chartData} 
                        options={chartOptions}
                      />
                      {eegData && (
                        <Text size="1" color="gray" style={{ 
                          position: 'absolute', 
                          bottom: '3px', 
                          right: '8px' 
                        }}>
                          {eegData.length} samples
                        </Text>
                      )}
                    </Box>
                  )}
                </Flex>
              </Card>
            </Box>
          </Flex>
        </Flex>
    </Card>
  );
}