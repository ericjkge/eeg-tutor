import { useState, useEffect } from 'react'
import { Theme, Button, Card, Text, Heading, TextField, TextArea, Select, Dialog, Flex, Box, Grid, Badge, IconButton } from '@radix-ui/themes'
import { PlusIcon, PlayIcon, TrashIcon } from '@radix-ui/react-icons'
import './App.css'

const API_BASE = 'http://localhost:8000'

function App() {
  const [activeTab, setActiveTab] = useState('decks')
  const [decks, setDecks] = useState([])
  const [selectedDeck, setSelectedDeck] = useState(null)
  const [currentCard, setCurrentCard] = useState(null)
  const [cardIndex, setCardIndex] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)
  const [newDeck, setNewDeck] = useState({ name: '', description: '' })
  const [newCard, setNewCard] = useState({ front: '', back: '', deck_id: 1 })
  const [showCreateDeckDialog, setShowCreateDeckDialog] = useState(false)

  // Fetch decks on component mount
  useEffect(() => {
    fetchDecks()
  }, [])

  const fetchDecks = async () => {
    try {
      const response = await fetch(`${API_BASE}/decks`)
      const data = await response.json()
      setDecks(data)
    } catch (error) {
      console.error('Failed to fetch decks:', error)
    }
  }

  const createDeck = async () => {
    if (!newDeck.name.trim()) return
    
    try {
      const response = await fetch(`${API_BASE}/decks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newDeck)
      })
      await response.json()
      setNewDeck({ name: '', description: '' })
      setShowCreateDeckDialog(false)
      fetchDecks()
    } catch (error) {
      console.error('Failed to create deck:', error)
    }
  }

  const createCard = async () => {
    if (!newCard.front.trim() || !newCard.back.trim()) return
    
    try {
      const response = await fetch(`${API_BASE}/cards`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCard)
      })
      await response.json()
      setNewCard({ front: '', back: '', deck_id: newCard.deck_id })
      fetchDecks() // Refresh to get updated deck with new card
    } catch (error) {
      console.error('Failed to create card:', error)
    }
  }

  const startStudying = (deck) => {
    setSelectedDeck(deck)
    setCardIndex(0)
    setCurrentCard(deck.cards[0] || null)
    setShowAnswer(false)
    setActiveTab('study')
  }

  const nextCard = () => {
    if (!selectedDeck || !selectedDeck.cards) return
    
    const nextIndex = (cardIndex + 1) % selectedDeck.cards.length
    setCardIndex(nextIndex)
    setCurrentCard(selectedDeck.cards[nextIndex])
    setShowAnswer(false)
  }

  const prevCard = () => {
    if (!selectedDeck || !selectedDeck.cards) return
    
    const prevIndex = cardIndex === 0 ? selectedDeck.cards.length - 1 : cardIndex - 1
    setCardIndex(prevIndex)
    setCurrentCard(selectedDeck.cards[prevIndex])
    setShowAnswer(false)
  }

  const flipCard = () => {
    setShowAnswer(!showAnswer)
  }

  return (
    <Theme>
      <div className="app">
        <header className="header">
          <Heading 
            size="6" 
            style={{ color: '#2563eb', cursor: 'pointer' }}
            onClick={() => setActiveTab('decks')}
          >
            Synapse
          </Heading>
          <nav className="nav-tabs">
            <Button 
              variant={activeTab === 'decks' ? 'solid' : 'soft'} 
              onClick={() => setActiveTab('decks')}
              size="3"
            >
              Decks
            </Button>
            <Button 
              variant={activeTab === 'add' ? 'solid' : 'soft'} 
              onClick={() => setActiveTab('add')}
              size="3"
            >
              Add Cards
            </Button>
            <Button 
              variant={activeTab === 'stats' ? 'solid' : 'soft'} 
              onClick={() => setActiveTab('stats')}
              size="3"
            >
              Stats
            </Button>
          </nav>
        </header>

      <main className="main-content">
        {activeTab === 'decks' && (
          <Box>
            <Flex justify="between" align="center" mb="4">
              <Heading size="5">My Decks</Heading>
              <Dialog.Root open={showCreateDeckDialog} onOpenChange={setShowCreateDeckDialog}>
                <Dialog.Trigger>
                  <IconButton variant="outline" size="3">
                    <PlusIcon width="18" height="18" />
                  </IconButton>
                </Dialog.Trigger>
                <Dialog.Content style={{ maxWidth: 450 }}>
                  <Dialog.Title>Create New Deck</Dialog.Title>
                  <Dialog.Description size="2" mb="4">
                    Add a new deck to organize your flashcards.
                  </Dialog.Description>
                  <Flex direction="column" gap="3">
                    <label>
                      <Text as="div" size="2" mb="1" weight="bold">
                        Deck Name
                      </Text>
                      <TextField.Input
                        placeholder="Enter deck name"
                        value={newDeck.name}
                        onChange={(e) => setNewDeck({...newDeck, name: e.target.value})}
                      />
                    </label>
                    <label>
                      <Text as="div" size="2" mb="1" weight="bold">
                        Description
                      </Text>
                      <TextField.Input
                        placeholder="Enter description (optional)"
                        value={newDeck.description}
                        onChange={(e) => setNewDeck({...newDeck, description: e.target.value})}
                      />
                    </label>
                  </Flex>
                  <Flex gap="3" mt="4" justify="end">
                    <Dialog.Close>
                      <Button variant="soft" color="gray">
                        Cancel
                      </Button>
                    </Dialog.Close>
                    <Button onClick={createDeck}>Create Deck</Button>
                  </Flex>
                </Dialog.Content>
              </Dialog.Root>
            </Flex>
            
            <Grid columns="3" gap="4" width="auto">
              {decks.map(deck => (
                <Card key={deck.id} size="2">
                  <Flex direction="column" gap="2">
                    <Heading size="4">{deck.name}</Heading>
                    <Text color="gray" size="2">{deck.description}</Text>
                    <Badge variant="soft" size="1">
                      {deck.cards.length} cards
                    </Badge>
                    <Button 
                      onClick={() => startStudying(deck)}
                      disabled={deck.cards.length === 0}
                      size="2"
                      style={{ marginTop: '8px' }}
                    >
                      <PlayIcon width="16" height="16" />
                      Study
                    </Button>
                  </Flex>
                </Card>
              ))}
            </Grid>
          </Box>
        )}

        {activeTab === 'add' && (
          <Box style={{ maxWidth: 600, margin: '0 auto' }}>
            <Card size="3">
              <Heading size="5" mb="4">Add New Card</Heading>
              <Flex direction="column" gap="4">
                <label>
                  <Text as="div" size="2" mb="2" weight="bold">
                    Select Deck
                  </Text>
                  <Select.Root 
                    value={newCard.deck_id.toString()}
                    onValueChange={(value) => setNewCard({...newCard, deck_id: parseInt(value)})}
                  >
                    <Select.Trigger />
                    <Select.Content>
                      {decks.map(deck => (
                        <Select.Item key={deck.id} value={deck.id.toString()}>
                          {deck.name}
                        </Select.Item>
                      ))}
                    </Select.Content>
                  </Select.Root>
                </label>
                
                <label>
                  <Text as="div" size="2" mb="2" weight="bold">
                    Front of Card
                  </Text>
                  <TextArea
                    placeholder="Enter the question or prompt"
                    value={newCard.front}
                    onChange={(e) => setNewCard({...newCard, front: e.target.value})}
                    rows={3}
                  />
                </label>
                
                <label>
                  <Text as="div" size="2" mb="2" weight="bold">
                    Back of Card
                  </Text>
                  <TextArea
                    placeholder="Enter the answer or explanation"
                    value={newCard.back}
                    onChange={(e) => setNewCard({...newCard, back: e.target.value})}
                    rows={3}
                  />
                </label>
                
                <Button onClick={createCard} size="3" style={{ marginTop: '8px' }}>
                  <PlusIcon width="16" height="16" />
                  Add Card
                </Button>
              </Flex>
            </Card>
          </Box>
        )}

        {activeTab === 'stats' && (
          <Box>
            <Heading size="5" mb="4">Statistics</Heading>
            <Grid columns="3" gap="4" width="auto">
              <Card size="3">
                <Flex direction="column" align="center" gap="2">
                  <Text size="2" color="gray" weight="medium">Total Decks</Text>
                  <Heading size="8" color="blue">{decks.length}</Heading>
                </Flex>
              </Card>
              <Card size="3">
                <Flex direction="column" align="center" gap="2">
                  <Text size="2" color="gray" weight="medium">Total Cards</Text>
                  <Heading size="8" color="blue">
                    {decks.reduce((total, deck) => total + deck.cards.length, 0)}
                  </Heading>
                </Flex>
              </Card>
              <Card size="3">
                <Flex direction="column" align="center" gap="2">
                  <Text size="2" color="gray" weight="medium">Cards Studied Today</Text>
                  <Heading size="8" color="blue">0</Heading>
                </Flex>
              </Card>
            </Grid>
          </Box>
        )}

        {activeTab === 'study' && currentCard && (
          <Box>
            <Flex justify="between" align="center" mb="4">
              <Heading size="5">{selectedDeck.name}</Heading>
              <Flex align="center" gap="4">
                <Text size="2" color="gray">
                  Card {cardIndex + 1} of {selectedDeck.cards.length}
                </Text>
                <Button variant="soft" onClick={() => setActiveTab('decks')}>
                  Back to Decks
                </Button>
              </Flex>
            </Flex>

             <Flex direction="column" align="center" gap="4">
               <Card size="4" style={{ minHeight: 250, width: '100%', maxWidth: 600 }}>
                 <Flex align="center" justify="center" style={{ minHeight: 200 }}>
                   <Text size="5" align="center" style={{ lineHeight: 1.6 }}>
                     {!showAnswer ? currentCard.front : currentCard.back}
                   </Text>
                 </Flex>
               </Card>
               
               {/* Combined button row */}
               <Flex gap="3" align="center">
                 <Button 
                   variant="outline" 
                   onClick={prevCard}
                   size="3"
                   style={{ width: '100px' }}
                 >
                   Previous
                 </Button>
                 <Button 
                   size="3" 
                   onClick={flipCard}
                   style={{ width: '100px' }}
                 >
                   Flip
                 </Button>
                 <Button 
                   variant="outline" 
                   onClick={nextCard}
                   size="3"
                   style={{ width: '100px' }}
                 >
                   Next
                 </Button>
               </Flex>
             </Flex>

            {/* Placeholder for EEG visualization */}
            <Card size="3" mt="6">
              <Heading size="4" mb="3">Brain Activity</Heading>
              <Box style={{ 
                height: 200, 
                backgroundColor: 'var(--gray-3)', 
                borderRadius: 'var(--radius-2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Text color="gray" style={{ fontStyle: 'italic' }}>
                  EEG visualization will go here
                </Text>
              </Box>
            </Card>
          </Box>
        )}
      </main>
    </div>
    </Theme>
  )
}

export default App