from opentrons import protocol_api


# metadata
metadata = {
    'protocolName': 'protocol_1(stage1_screening)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Protocol for broad screen of substrates across 2 plates',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip racks
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
    tiprack3 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    tiprack4 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)

    # Stock solution plates
    stock96 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5) # Substrates
    stock12 = protocol.load_labware('mettlertoledo_12_reservoir_24000ul', 6) # TFA solutions, HFIP, and reagents

    # Reaction plates
    plate1 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 7)
    plate2 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 8)
    plate3 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 10)
    plate4 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 11)
    plates = [plate1, plate2, plate3, plate4]
    
    # Pipette
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2, tiprack3, tiprack4])


    # STOCK SOLUTIONS

    substrates = stock96.rows()[0][0:4] # Substrate stock solution locations - A1, B1, C1, D1: The first four columns of the stock96 plate
    tfa = stock12.wells()[0:3] # HFIP and TFA solution locations
    halogens = stock12.wells()[3:7] # Halogenating reagent locations


    # DISPENSE FUNCTIONS

    def premulti(solution): # Procedure to "prepare" each tip before use, ensuring accurate and consistent handling on solutions
        protocol.max_speeds['Z'] = 200 # Set the z-axis speed to 200 mm/s when prepareing tips
        multi.pick_up_tip()
        
        # Pre-wetting of tip
        for k in range (2):
            multi.aspirate(100, solution) # Aspirate 100uL of solution from the source well
            multi.move_to(solution.top()) # Move to the top of the source well
            protocol.delay(seconds = 5) # Delay for 5 seconds
            multi.dispense(100, solution.top()) # Dispense 100uL of solution back into the source well
            multi.blow_out() # Blow out any remaining solution in/on the pipette tip
            
        # Pre-saturation
        multi.move_to(solution.bottom(1)) # Move to the bottom of the source well
        multi.mix(2, 100) # Aspitate and dispense 100uL of solution 2 times
            
        protocol.max_speeds['Z'] = 80 # Set the z-axis speed to 80 mm/s when performing disepenses


    def liq_hand(vol, asp_well, dis_well): # Procedure to handle liquid transfers
        if count[0] == -1: # If the tips attached have not been used, prepare the tips 
            premulti(asp_well)
            count[0] = 0
        if count[0] == 4: # If the tips attached have been used 4 times, drop tips in the trash and prepare new tips
            multi.drop_tip()        
            count[0] = 0
            premulti(asp_well)
                    
        multi.aspirate(vol, asp_well, rate = 0.5) # Aspirate a specified volume of solution from a source well at a specified height at half the default rate (default rate = 94 uL/s)
        multi.dispense(vol, dis_well.top(), rate = 0.5) # Dispense a specified volume of solution at the top of the destination well at half the default rate (default rate = 94 uL/s)
        multi.blow_out() # Blow out any remaining solution in/on the pipette tip

        count[0] = count[0] + 1 # Add 1 to the dispense count (used to determine when to drop tips and prepare new tips)

    
    # DISPENSE PROTOCOL

    count = [-1]

    # Substrate dispenses
    for substrate, plate in zip(substrates, plates):
        for j in range(12):
            liq_hand(100, substrate, plate.rows()[0][j]) # Dispense 100 uL of each column of substrates in stock96 across each individual plates

    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]

    # TFA/HFIP dispenses

    for i, acid in enumerate(tfa): 
        for plate in plates:
            for j in range(4):
                liq_hand(60, acid, plate.rows()[0][3*j+i]) # Dispensed 60 uL of HFIP or a TFA stock solution across a plate in a repeating pattern (HFIP, TFA (0.33 M), TFA (1.67 M), etc.....)
 
    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]

    # Halogenating reagent dispenses
    for i, halogen in enumerate(halogens):
        for plate in plates:
            for j in range(3):
                liq_hand(40, halogen, plate.rows()[0][3*i+j]) # Dispensed 40 uL of each halogenating reagent across a plate in blocks of 3 (NBS, NBS, NBS, NIS, NIS, NIS, etc.....)
        
    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]
