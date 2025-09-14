import { useState, useEffect } from 'react';
import { Button, Flex, Box, Heading, Text, Progress, Card, Spinner, Avatar, Badge } from '@radix-ui/themes';
import { FaCircleCheck } from 'react-icons/fa6';
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
  }, [currentTestIndex, sessionId, tests]);

  const currentTest = tests[currentTestIndex];
  const isLastTest = currentTestIndex === tests.length - 1;

  const handleAnswerSelect = (choice) => {
    setSelectedAnswer(choice);
  };

  // EEG snapshot function (single latest sample)
  const saveEEGSnapshot = async (sessionId, questionId) => {
    try {
      const response = await fetch(`http://localhost:8000/eeg/snapshot?session_id=${sessionId}&question_id=${questionId}`, {
        method: 'POST'
      });
      const result = await response.json();
      console.log('EEG snapshot response:', result);
      return result.success;
    } catch (error) {
      console.error('Error saving EEG snapshot:', error);
      return false;
    }
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
      // Use existing session ID (should always exist by this point)
      if (!sessionId) {
        console.error('No session ID available when trying to save answer');
        return false;
      }

      const resp = await fetch('http://localhost:8000/calibration/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
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
      // Save single latest EEG sample for this question
      if (sessionId && currentTest?.id) {
        await saveEEGSnapshot(sessionId, currentTest.id);
      }

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
  const [trainingData, setTrainingData] = useState(null);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingComplete, setTrainingComplete] = useState(false);
  const [trainingResult, setTrainingResult] = useState(null);

  useEffect(() => {
    // Load training data preview
    const loadTrainingData = async () => {
      try {
        const response = await fetch('http://localhost:8000/ml/training-data');
        const data = await response.json();
        if (data.success) {
          setTrainingData(data);
        } else {
          console.error('Failed to load training data:', data.error);
        }
      } catch (error) {
        console.error('Error loading training data:', error);
      } finally {
        setIsLoadingData(false);
      }
    };

    loadTrainingData();
  }, []);

  const handleTrainModel = async () => {
    setIsTraining(true);
    
    // Start training and minimum 3 second timer in parallel
    const [result] = await Promise.all([
      // Training API call
      (async () => {
        try {
          const response = await fetch('http://localhost:8000/ml/train', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              validation_split: 0.2,
              save_as_new_version: true
            })
          });
          return await response.json();
        } catch (error) {
          console.error('Error training model:', error);
          return { success: false, error: error.message };
        }
      })(),
      // Minimum 3 second delay
      new Promise(resolve => setTimeout(resolve, 3000))
    ]);

    setTrainingResult(result);
    
    if (result.success) {
      setTrainingComplete(true);
    } else {
      console.error('Training failed:', result.error);
    }
    
    setIsTraining(false);
  };

  if (isLoadingData) {
    return (
      <Card size="4" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <Flex direction="column" gap="4" align="center">
          <Heading size="6">Train the Model</Heading>
          <Spinner size="3" />
          <Text size="3" color="gray">Loading training data...</Text>
        </Flex>
      </Card>
    );
  }

  return (
    <Card size="4" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <Flex direction="column" gap="4">
        <Heading size="6">Train the Model</Heading>
        
        {!isTraining && !trainingComplete && (
          <>
            {/* Data Preview */}
            {trainingData && (
              <Card style={{ 
                padding: '12px',
                backgroundColor: 'var(--gray-2)', 
                borderRadius: 'var(--radius-3)'
              }}>
                <Heading size="4" style={{ marginBottom: '8px' }}>Training Data Summary</Heading>
                <Flex direction="column" gap="2">
                  <Flex justify="between" align="center">
                    <Flex gap="4">
                      <Text size="2" color="gray">Sessions: <strong>{trainingData.summary.total_sessions}</strong></Text>
                      <Text size="2" color="gray">EEG: <strong>{trainingData.summary.total_eeg_samples}</strong></Text>
                      <Text size="2" color="gray">Pairs: <strong>{trainingData.summary.total_training_pairs}</strong></Text>
                    </Flex>
                    <Flex gap="1">
                      {Object.entries(trainingData.summary.difficulty_distribution).map(([difficulty, count]) => (
                        <Badge key={difficulty} size="1" color={
                          difficulty === 'easy' ? 'green' : 
                          difficulty === 'medium' ? 'orange' : 'red'
                        }>
                          {difficulty}: {count}
                        </Badge>
                      ))}
                    </Flex>
                  </Flex>
                </Flex>
              </Card>
            )}

            {/* Recent Samples Preview */}
            {trainingData?.recent_samples && trainingData.recent_samples.length > 0 && (
              <Card style={{ 
                padding: '12px',
                backgroundColor: 'var(--gray-2)', 
                borderRadius: 'var(--radius-3)'
              }}>
                <Heading size="4" style={{ marginBottom: '8px' }}>Recent EEG-Response Pairs</Heading>
                <Flex direction="column" gap="2">
                  {trainingData.recent_samples.slice(0, 3).map((sample, index) => (
                    <Flex key={index} justify="between" align="center" style={{
                      padding: '6px',
                      backgroundColor: 'var(--gray-3)',
                      borderRadius: 'var(--radius-2)'
                    }}>
                      <Flex direction="column">
                        <Text size="2" weight="medium">
                          Q{sample.question_id} - {sample.difficulty}
                        </Text>
                        <Text size="1" color="gray">
                          EEG: {sample.tp9?.toFixed(2)}, {sample.af7?.toFixed(2)}, {sample.af8?.toFixed(2)}, {sample.tp10?.toFixed(2)}
                        </Text>
                      </Flex>
                      <Badge color={sample.is_correct ? 'green' : 'red'} variant="soft">
                        {sample.is_correct ? '✓' : '✗'}
                      </Badge>
                    </Flex>
                  ))}
                </Flex>
              </Card>
            )}
          </>
        )}

        {/* Training in Progress */}
        {isTraining && (
          <Card style={{ 
            height: '150px', 
            backgroundColor: 'var(--accent-2)', 
            borderRadius: 'var(--radius-3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Flex direction="column" align="center" gap="4">
              <Box style={{ position: 'relative', width: '80px', height: '80px' }}>
                {/* Core circle */}
                <Box style={{
                  position: 'absolute',
                  top: '55%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--accent-9)',
                }} />
                
                {/* Pulsing rings */}
                <Box style={{
                  position: 'absolute',
                  top: '55%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  border: '2px solid var(--accent-9)',
                  animation: 'pulse-ring 2.5s infinite',
                  animationDelay: '0s'
                }} />
                
                <Box style={{
                  position: 'absolute',
                  top: '55%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  border: '2px solid var(--accent-9)',
                  animation: 'pulse-ring 2.5s infinite',
                  animationDelay: '-0.8s'
                }} />
                
                <Box style={{
                  position: 'absolute',
                  top: '55%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  border: '2px solid var(--accent-9)',
                  animation: 'pulse-ring 2.5s infinite',
                  animationDelay: '-1.6s'
                }} />
              </Box>
              <Text size="4" weight="medium" style={{ color: 'var(--accent-9)' }}>Training Model...</Text>
            </Flex>
          </Card>
        )}

        {/* Training Complete */}
        {trainingComplete && trainingResult && (
          <Card style={{ 
            padding: '20px',
            backgroundColor: 'var(--accent-2)', 
            borderRadius: 'var(--radius-3)',
            border: '1px solid var(--accent-6)'
          }}>
            <Flex direction="column" align="center" gap="4">
              <FaCircleCheck 
                size={48} 
                style={{ color: 'var(--accent-9)' }}
              />
              <Text size="4" weight="medium" style={{ color: 'var(--accent-9)' }}>
                Model Training Complete!
              </Text>
              
              {trainingResult.success && (
                <Flex direction="column" gap="2" style={{ width: '100%' }}>
                  <Flex justify="between">
                    <Text size="3" color="gray">Model Version:</Text>
                    <Badge color="blue">v{trainingResult.model_version}</Badge>
                  </Flex>
                  <Flex justify="between">
                    <Text size="3" color="gray">Training Samples:</Text>
                    <Badge variant="outline">{trainingResult.training_metrics.n_samples}</Badge>
                  </Flex>
                   <Flex justify="between">
                     <Text size="3" color="gray">Test Accuracy (MAE):</Text>
                     <Badge variant="outline">
                       {trainingResult.training_metrics.test_mae != null ? 
                         trainingResult.training_metrics.test_mae.toFixed(3) : 'N/A'}
                     </Badge>
                   </Flex>
                  {trainingResult.training_metrics.difficulty_distribution && (
                    <Box style={{ marginTop: '8px' }}>
                      <Text size="3" color="gray" style={{ marginBottom: '4px' }}>Trained on:</Text>
                      <Flex gap="2">
                        {Object.entries(trainingResult.training_metrics.difficulty_distribution).map(([difficulty, count]) => (
                          <Badge key={difficulty} variant="soft" color={
                            difficulty === 'easy' ? 'green' : 
                            difficulty === 'medium' ? 'orange' : 'red'
                          }>
                            {count} {difficulty}
                          </Badge>
                        ))}
                      </Flex>
                    </Box>
                  )}
                </Flex>
              )}
            </Flex>
          </Card>
        )}

        {/* Navigation */}
        {!trainingComplete ? (
          <Flex gap="3">
            <Button variant="outline" onClick={onPrev} disabled={isTraining} style={{ height: '40px' }}>
              Back
            </Button>
            <Button 
              size="3" 
              onClick={handleTrainModel}
              disabled={isTraining || !trainingData?.summary?.total_training_pairs}
              style={{ flex: 1, height: '40px' }}
            >
              {isTraining ? 'Training...' : 'Train Model'}
            </Button>
          </Flex>
        ) : (
          <Button 
            size="3" 
            onClick={onNext}
            style={{ width: '100%', height: '40px' }}
          >
            Continue to Practice
          </Button>
        )}
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
