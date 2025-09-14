import { useState } from 'react';
import { Button, Flex, Box, Heading, Text, Progress, Card } from '@radix-ui/themes';
import { FaCircleNodes } from 'react-icons/fa6';

const stages = [
  { id: 1, name: 'Connect', title: 'Connect Your Device' },
  { id: 2, name: 'Calibrate', title: 'Calibrate Your Brainwaves' },
  { id: 3, name: 'Train', title: 'Train the Model' }
];

function ConnectStage({ onNext }) {
  return (
    <Card size="4" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <Flex direction="column" gap="4" align="center">
        <Heading size="6">Connect Your EEG Device</Heading>
        <Text size="4" color="gray" style={{ textAlign: 'center' }}>
          Connect your EEG headset to begin capturing brainwave data. 
          Make sure your device is properly positioned and powered on.
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
            Device connection interface will go here
          </Text>
        </Box>
        <Button size="3" onClick={onNext} style={{ height: '40px' }}>
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
          <FaCircleNodes 
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
