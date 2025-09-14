import { useState, useEffect } from 'react';
import { Button, Flex, Box, Heading, Text, Progress, Card, Spinner, Avatar } from '@radix-ui/themes';
import { FaBrain, FaCircleCheck } from 'react-icons/fa6';
import { SiAmazonluna } from 'react-icons/si';

const stages = [
  { id: 1, name: 'Connect', title: 'Connect Your Device' },
  { id: 2, name: 'Calibrate', title: 'Calibrate Your Brainwaves' },
  { id: 3, name: 'Train', title: 'Train the Model' }
];

function ConnectStage({ onNext }) {
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Start EEG service when component mounts
    const startEEGService = async () => {
      try {
        await fetch('http://localhost:8000/eeg/start', { method: 'POST' });
      } catch (error) {
        console.error('Failed to start EEG service:', error);
      }
    };

    startEEGService();

    // Poll for connection status
    const pollStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/eeg/status');
        const status = await response.json();
        setConnectionStatus(status);
        setIsConnected(status.is_connected);
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to check EEG status:', error);
        setIsLoading(false);
      }
    };

    // Poll every 500ms for connection status
    const interval = setInterval(pollStatus, 500);
    pollStatus(); // Initial call

    return () => clearInterval(interval);
  }, []);


  return (
    <Card size="4" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <Flex direction="column" gap="4" align="center">
        <Heading size="6">Connect Your EEG Device</Heading>
        <Text size="4" color="gray" style={{ textAlign: 'center' }}>
          Connect your EEG headset to begin capturing brainwave data. 
          Make sure your device is properly positioned and powered on.
        </Text>

        <Card style={{ 
          height: '240px', 
          width: '100%', 
          backgroundColor: 'var(--gray-2)', 
          borderRadius: 'var(--radius-3)',
          padding: '20px'
        }}>
          <Flex direction="column" align="center" justify="center" gap="4" style={{ height: '100%' }}>
            {isLoading ? (
              <>
                <Spinner size="3" />
                <Text size="3" color="gray">Initializing EEG service...</Text>
              </>
            ) : isConnected ? (
              <>
                <FaCircleCheck 
                  size={60} 
                  style={{ color: 'var(--green-9)' }}
                />
                <Text size="4" weight="medium" color="green">Device Connected!</Text>
                <Text size="2" color="gray" style={{ textAlign: 'center' }}>
                  Sample Rate: {connectionStatus?.sample_rate || 0} Hz<br/>
                  Data Points: {connectionStatus?.data_count || 0}
                </Text>
              </>
              ) : (
                <>
                  <Spinner size="3" />
                  <Text size="4" weight="medium" color="gray">Waiting for EEG device...</Text>
                  <Text size="2" color="gray" style={{ textAlign: 'center' }}>
                    Make sure your Muse streaming app is<br/>
                    configured to send OSC to <strong>localhost:8001</strong>
                  </Text>
                </>
              )}
          </Flex>
        </Card>

        <Button 
          size="3" 
          onClick={onNext} 
          disabled={!isConnected}
          style={{ height: '40px' }}
        >
          Continue to Calibration
        </Button>
      </Flex>
    </Card>
  );
}

function CalibrateStage({ onNext, onPrev }) {
  return (
    <Card size="4" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <Flex direction="column" gap="4" align="center">
        <Heading size="6">Calibrate Your Brainwaves</Heading>
        <Text size="4" color="gray" style={{ textAlign: 'center' }}>
          Follow the calibration exercises to establish your baseline brainwave patterns.
          This helps us understand your unique neural signatures.
        </Text>
        <Box style={{ 
          height: '200px', 
          width: '100%', 
          backgroundColor: 'var(--gray-3)', 
          borderRadius: 'var(--radius-3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Text size="3" color="gray" style={{ fontStyle: 'italic' }}>
            Calibration exercises will go here
          </Text>
        </Box>
        <Flex gap="3">
          <Button variant="outline" onClick={onPrev} style={{ height: '40px' }}>
            Back
          </Button>
          <Button size="3" onClick={onNext} style={{ height: '40px' }}>
            Continue to Training
          </Button>
        </Flex>
      </Flex>
    </Card>
  );
}

function TrainStage({ onNext, onPrev }) {
  return (
    <Card size="4" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <Flex direction="column" gap="4" align="center">
        <Heading size="6">Train the Model</Heading>
        <Text size="4" color="gray" style={{ textAlign: 'center' }}>
          Complete training sessions to teach the AI model to recognize your learning states.
          This process will improve over time with more data.
        </Text>
        <Box style={{ 
          height: '200px', 
          width: '100%', 
          backgroundColor: 'var(--gray-3)', 
          borderRadius: 'var(--radius-3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Text size="3" color="gray" style={{ fontStyle: 'italic' }}>
            Training interface will go here
          </Text>
        </Box>
        <Flex gap="3">
          <Button variant="outline" onClick={onPrev} style={{ height: '40px' }}>
            Back
          </Button>
          <Button size="3" onClick={onNext} style={{ height: '40px' }}>
            Start Learning
          </Button>
        </Flex>
      </Flex>
    </Card>
  );
}

export function TrainingWizard({ onComplete, onGoHome }) {
  const [currentStage, setCurrentStage] = useState(1);

  const handleNext = () => {
    if (currentStage < 3) {
      setCurrentStage(currentStage + 1);
    } else {
      onComplete();
    }
  };

  const handlePrev = () => {
    if (currentStage > 1) {
      setCurrentStage(currentStage - 1);
    }
  };

  const currentStageData = stages.find(stage => stage.id === currentStage);
  const progressValue = (currentStage / stages.length) * 100;

  return (
    <Box 
      style={{ 
        minHeight: '100vh',
        width: '100vw',
        background: 'var(--gray-1)'
      }}
    >
      {/* Synapse branding in upper left */}
      <Box style={{ 
        position: 'fixed', 
        top: '2rem', 
        left: '2rem',
        zIndex: 1000
      }}>
        <Flex align="center" gap="2" style={{ cursor: 'pointer' }} onClick={onGoHome}>
          <SiAmazonluna 
            size={24} 
            style={{ color: 'var(--accent-9)' }}
          />
          <Heading 
            size="6" 
            style={{ 
              color: 'var(--accent-9)',
              fontWeight: 'bold'
            }}
          >
            Synapse
          </Heading>
        </Flex>
      </Box>

      {/* Header with progress */}
      <Box style={{ 
        padding: '2rem', 
        paddingTop: '6rem',
        maxWidth: '800px', 
        margin: '0 auto' 
      }}>
        <Flex direction="column" gap="4" align="center">
          <Heading 
            size="8" 
            style={{ 
              textAlign: 'center'
            }}
          >
            {currentStageData.title}
          </Heading>
          
          {/* Progress indicators */}
          <Flex gap="6" align="center" style={{ marginBottom: '2rem' }}>
            {stages.map((stage) => (
              <Flex key={stage.id} direction="column" align="center" gap="3">
                <Box
                  style={{
                    width: '50px',
                    height: '50px',
                    borderRadius: '50%',
                    backgroundColor: stage.id <= currentStage ? 'var(--accent-9)' : 'var(--gray-6)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 'bold',
                    fontSize: '1.1rem'
                  }}
                >
                  {stage.id}
                </Box>
                <Text 
                  size="3" 
                  weight={stage.id === currentStage ? 'bold' : 'medium'}
                  color={stage.id === currentStage ? 'accent' : 'gray'}
                >
                  {stage.name}
                </Text>
              </Flex>
            ))}
          </Flex>

          <Progress value={progressValue} style={{ width: '300px' }} />
        </Flex>
      </Box>

      {/* Main content */}
      <Box style={{ padding: '2rem' }}>
        {currentStage === 1 && <ConnectStage onNext={handleNext} />}
        {currentStage === 2 && <CalibrateStage onNext={handleNext} onPrev={handlePrev} />}
        {currentStage === 3 && <TrainStage onNext={handleNext} onPrev={handlePrev} />}
      </Box>
    </Box>
  );
}
