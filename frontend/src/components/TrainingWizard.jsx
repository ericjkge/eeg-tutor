import { useState, useEffect } from 'react';
import { Button, Flex, Box, Heading, Text, Progress, Card, Spinner, Avatar, Badge } from '@radix-ui/themes';
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
                  style={{ color: 'var(--accent-9)' }}
                />
                <Text size="4" weight="medium" style={{ color: 'var(--accent-9)' }}>Device Connected!</Text>
                <Text size="2" color="gray" style={{ textAlign: 'center' }}>
                  Sample Rate: {connectionStatus?.sample_rate || 0} Hz<br/>
                  Data Points: {connectionStatus?.data_count || 0}
                </Text>
              </>
              ) : (
                <>
                  <Box style={{ position: 'relative', width: '100px', height: '100px' }}>
                    {/* Core circle */}
                    <Box style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: '16px',
                      height: '16px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--accent-9)',
                    }} />
                    
                    {/* Pulsing rings */}
                    <Box style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: '30px',
                      height: '30px',
                      borderRadius: '50%',
                      border: '3px solid var(--accent-9)',
                      animation: 'pulse-ring 2.5s infinite',
                      animationDelay: '0s'
                    }} />
                    
                    <Box style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: '30px',
                      height: '30px',
                      borderRadius: '50%',
                      border: '3px solid var(--accent-9)',
                      animation: 'pulse-ring 2.5s infinite',
                      animationDelay: '-0.8s'
                    }} />
                    
                    <Box style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      width: '30px',
                      height: '30px',
                      borderRadius: '50%',
                      border: '3px solid var(--accent-9)',
                      animation: 'pulse-ring 2.5s infinite',
                      animationDelay: '-1.6s'
                    }} />
                  </Box>
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
          disabled={false}
          style={{ height: '40px' }}
        >
          Continue to Calibration
        </Button>
      </Flex>
    </Card>
  );
}

function CalibrateStage({ onNext, onPrev }) {
  const [tests, setTests] = useState([]);
  const [currentTestIndex, setCurrentTestIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [answers, setAnswers] = useState([]);
  const [startTime, setStartTime] = useState(Date.now());
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    // Load calibration tests from backend
    const loadTests = async () => {
      try {
        const response = await fetch('http://localhost:8000/calibration/tests');
        const data = await response.json();
        if (data.tests) {
          setTests(data.tests);
          setIsLoading(false);
          setStartTime(Date.now()); // Reset start time when question loads
          // Start a calibration session for per-question saving
          try {
            const startResp = await fetch('http://localhost:8000/calibration/start', {
              method: 'POST'
            });
            const startData = await startResp.json();
            if (startData?.session_id) {
              setSessionId(startData.session_id);
            }
          } catch (e) {
            console.error('Failed to start calibration session:', e);
          }
        }
      } catch (error) {
        console.error('Failed to load calibration tests:', error);
        setIsLoading(false);
      }
    };

    loadTests();
  }, []);

  // Reset start time when moving to next question
  useEffect(() => {
    setStartTime(Date.now());
  }, [currentTestIndex]);

  const currentTest = tests[currentTestIndex];
  const isLastTest = currentTestIndex === tests.length - 1;

  const handleAnswerSelect = (choice) => {
    setSelectedAnswer(choice);
  };

  const submitCalibrationData = async (allAnswers) => {
    try {
      const response = await fetch('http://localhost:8000/calibration/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          responses: allAnswers,
          sessionData: {
            userAgent: navigator.userAgent,
            completedAt: new Date().toISOString()
          }
        })
      });

      const result = await response.json();
      if (result.success) {
        console.log('✅ Calibration data saved to database:', result.message);
      } else {
        console.error('❌ Failed to save calibration data:', result);
      }
    } catch (error) {
      console.error('❌ Error submitting calibration data:', error);
    }
  };

  const saveAnswer = async (record) => {
    try {
      // Ensure we have a session; start if missing
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        const startResp = await fetch('http://localhost:8000/calibration/start', { method: 'POST' });
        const startData = await startResp.json();
        currentSessionId = startData?.session_id;
        setSessionId(currentSessionId);
      }

      if (!currentSessionId) return false;

      const resp = await fetch('http://localhost:8000/calibration/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: currentSessionId,
          testId: record.testId,
          question: record.question,
          difficulty: record.difficulty,
          selectedAnswer: record.selectedAnswer,
          correctAnswer: record.correctAnswer,
          isCorrect: record.isCorrect,
          timestamp: record.timestamp,
          timeSpent: record.timeSpent
        })
      });
      const result = await resp.json();
      if (!result?.success) {
        console.error('Failed to save answer:', result);
        return false;
      }
      return true;
    } catch (e) {
      console.error('Error saving answer:', e);
      return false;
    }
  };

  const completeSession = async () => {
    try {
      if (!sessionId) return;
      await fetch(`http://localhost:8000/calibration/complete?session_id=${sessionId}`, { method: 'POST' });
    } catch (e) {
      console.error('Error completing session:', e);
    }
  };

  const handleNext = async () => {
    if (selectedAnswer) {
      // Record the answer with timestamp for EEG correlation
      const answerRecord = {
        testId: currentTest.id,
        question: currentTest.question,
        difficulty: currentTest.difficulty,
        selectedAnswer,
        correctAnswer: currentTest.answer,
        isCorrect: selectedAnswer === currentTest.answer,
        timestamp: Date.now(),
        timeSpent: Date.now() - startTime
      };
      
      setAnswers([...answers, answerRecord]);
      
      if (isLastTest) {
        // Save final answer and complete the session
        await saveAnswer(answerRecord);
        await completeSession();
        onNext();
      } else {
        // Save answer and move to next test
        await saveAnswer(answerRecord);
        setCurrentTestIndex(currentTestIndex + 1);
        setSelectedAnswer(null);
      }
    }
  };

  if (isLoading) {
    return (
      <Card size="4" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <Flex direction="column" gap="4" align="center">
          <Heading size="6">Loading Calibration Tests...</Heading>
          <Spinner size="3" />
        </Flex>
      </Card>
    );
  }

  if (!currentTest) {
    return (
      <Card size="4" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <Flex direction="column" gap="4" align="center">
          <Heading size="6">Error</Heading>
          <Text>Failed to load calibration tests.</Text>
          <Button variant="outline" onClick={onPrev}>Back</Button>
        </Flex>
      </Card>
    );
  }

  return (
    <Card size="4" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <Flex direction="column" gap="4">
        {/* Header */}
        <Flex justify="between" align="center">
          <Heading size="6">Calibration</Heading>
          <Text size="2" color="gray">
            {currentTestIndex + 1} of {tests.length}
          </Text>
        </Flex>

        {/* Question */}
        <Box style={{ 
          padding: '16px',
          backgroundColor: 'var(--gray-2)',
          borderRadius: 'var(--radius-3)',
          textAlign: 'center'
        }}>
          <Text size="5" weight="medium">
            {currentTest.question}
          </Text>
        </Box>

        {/* Answer Choices */}
        <Flex direction="column" gap="3">
          {currentTest.choices.map((choice, index) => (
            <Button
              key={index}
              variant={selectedAnswer === choice ? "solid" : "outline"}
              size="3"
              onClick={() => handleAnswerSelect(choice)}
              style={{ 
                justifyContent: 'flex-start',
                padding: '16px',
                height: 'auto'
              }}
            >
              <Text size="4">{choice}</Text>
            </Button>
          ))}
        </Flex>

        {/* Navigation */}
        <Flex gap="3">
          <Button variant="outline" onClick={onPrev} style={{ height: '40px' }}>
            Back
          </Button>
          <Button 
            size="3" 
            onClick={handleNext}
            disabled={!selectedAnswer}
            style={{ flex: 1, height: '40px' }}
          >
            {isLastTest ? 'Complete Calibration' : 'Next Question'}
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
