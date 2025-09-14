import { Button, Flex, Box, Heading, Text } from '@radix-ui/themes';
import { FaCircleNodes } from 'react-icons/fa6';
import { AuroraText } from './AuroraText';

export function Welcome({ onGetStarted }) {
  return (
    <Box 
      style={{ 
        minHeight: '100vh',
        width: '100vw',
        background: 'linear-gradient(135deg, var(--blue-1) 0%, var(--purple-1) 100%)',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Synapse branding in upper left */}
      <Box style={{ 
        position: 'absolute', 
        top: '2rem', 
        left: '2rem',
        zIndex: 10
      }}>
        <Flex align="center" gap="2">
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

      {/* Main content centered */}
      <Flex 
        direction="column" 
        align="center" 
        justify="center" 
        style={{ 
          minHeight: '100vh',
          width: '100%',
          padding: '2rem'
        }}
      >
        <Box style={{ textAlign: 'center', maxWidth: '800px' }}>
          <Heading 
            size="9" 
            style={{ 
              marginBottom: '2rem',
              lineHeight: 1.2,
              fontSize: 'clamp(2.5rem, 8vw, 4.5rem)',
              textAlign: 'center'
            }}
          >
            <div>
              Learn{' '}
              <AuroraText 
                className="inline-block"
                colors={["#2563eb", "#7c3aed", "#0ea5e9", "#06b6d4"]}
                speed={1.5}
              >
                smarter
              </AuroraText>
            </div>
            <div>through your brainwaves</div>
          </Heading>
          
          <Button 
            size="4" 
            onClick={onGetStarted}
            style={{ 
              marginTop: '3rem',
              padding: '1.2rem 2.5rem',
              fontSize: '1.3rem',
              cursor: 'pointer'
            }}
          >
            Get started
          </Button>
        </Box>
      </Flex>
    </Box>
  );
}
