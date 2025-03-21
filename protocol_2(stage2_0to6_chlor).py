from opentrons import protocol_api


# metadata
metadata = {
    'protocolName': 'protocol_2(stage2_0to6_chlor)',
    'author': 'Callum R. John <crj21@ic.ac.uk>',
    'description': 'Stage 2 screening of chlorinations (0-6 TFA equivalents)',
    'apiLevel': '2.9'
}

def run(protocol: protocol_api.ProtocolContext):
    
    # LABWARE

    # Pipette tip racks
    tiprack1 = protocol.load_labware('opentrons_96_tiprack_300ul', 1)
    tiprack2 = protocol.load_labware('opentrons_96_tiprack_300ul', 4)
    
    # Stock solution plates
    stock8 = protocol.load_labware('mettlertoledo_8_reservoir_36000ul', 2) # Substrates
    stock12 = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 5) # TFA soltutions, HFIP, and halogenating reagent
    
    # Reaction plate
    plate = protocol.load_labware('2mlcollection_96_wellplate_2000ul', 3)

    # Pipette
    multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks = [tiprack1, tiprack2])
    protocol.max_speeds['X'] = 200
    protocol.max_speeds['Y'] = 200



    # STOCK SOLUTIONS
    # acid_0 - 0.05 M TFA, acid_1 - 0.5 M TFA, acid_2 - 2.0 M TFA
    acid_no = {0: {'stock': None, 'vol': 0}, # control (no acid)
               2: {'stock': None, 'vol': 0}} # 0 equiv
    acid_0 = {3: {'stock': stock12['A6'], 'vol': 40}} # 0.1 equiv
    acid_1 = {4: {'stock': stock12['A7'], 'vol': 20}, # 0.5 equiv
              5: {'stock': stock12['A7'], 'vol': 40}, # 1 equiv
              6: {'stock': stock12['A7'], 'vol': 60}} # 1.5 equiv
    acid_2 = {1: {'stock': stock12['A8'], 'vol': 20}, # 2 equiv control
              7: {'stock': stock12['A8'], 'vol': 20}, # 2 equiv
              8: {'stock': stock12['A8'], 'vol': 30}, # 3 equiv
              9: {'stock': stock12['A8'], 'vol': 40}, # 4 equiv
              10: {'stock': stock12['A8'], 'vol': 50}, # 5 equiv
              11: {'stock': stock12['A8'], 'vol': 60}} # 6 equiv

    # Combine dictionaries into one
    acid = {}
    acid.update(acid_no)
    acid.update(acid_0)
    acid.update(acid_1)
    acid.update(acid_2)
    aciddis = [acid_0, acid_1, acid_2]

    
    # DISPENSE FUNCTIONS

    def premulti(solution):
        protocol.max_speeds['Z'] = 200 # Set the z-axis speed to 200 mm/s when prepareing tips
        multi.pick_up_tip()
        
        # PRE-WETTING OF TIP
        for k in range (2):
            multi.aspirate(100, solution) # Aspirate 100uL of solution from the source well
            multi.move_to(solution.top()) # Move to the top of the source well
            protocol.delay(seconds = 5) # Delay for 5 seconds
            multi.dispense(100, solution.top()) # Dispense 100uL of solution back into the source well
            
        # PRE-SATURATION
        multi.move_to(solution.bottom(1)) # Move to the bottom of the source well
        multi.mix(2, 100) # Aspirate and dispense 100uL of solution 2 times
            
        protocol.max_speeds['Z'] = 50 # Set the z-axis speed to 50 mm/s when performing dispenses


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

    count = [-1] # Initialise the dispense count to -1 (used to determine when to drop tips and prepare new tips)
    
    # Substrate dispenses
    for i in range(12):
        liq_hand(100, stock8['A1'], plate.rows()[0][i]) # Dispense 100 uL of each substrate across the plate

    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]


    # HFIP dispenses
    for wells in acid: # Add 40 uL of HFIP to each control (in lieu of Palau'chlor stock)
        if wells == 0 or wells == 1:
            extra = 40 
        else:
            extra = 0
        
        if acid[wells]['vol'] < 60: # If the well is not a control...
            liq_hand(60 - acid[wells]['vol'] + extra, stock12['A5'], plate.rows()[0][wells]) # Dispense HFIP solution across the plate according to the hfip_quantities dictionary

    if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
        multi.drop_tip()
    count = [-1]


    # TFA dispenses
    for acids in aciddis:
        for wells in acids:
            liq_hand(acid[wells]['vol'], acid[wells]['stock'], plate.rows()[0][wells]) # Dispense TFA stock solutions across the plate according to the acid dictionary (stock solution and volume information)
        
        if count[0] != 0: # Reset the tip count and drop tips if used tips are attached
            multi.drop_tip()
        count = [-1]


    # Palau'chlor dispenses
    for i in range(10):
        liq_hand(40, stock12.wells()[0], plate.rows()[0][i+2]) # Dispense 40 uL of Palau'chlor across the plate
        
    if count[0] != 0: # Drop tips if used tips are attached
        multi.drop_tip()