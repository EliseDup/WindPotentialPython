import sys
import numpy as np
from numpy import genfromtxt, ndarray
import math
from datetime import datetime
from scipy.special import gammainc
from matplotlib.pyplot import plot

inputs_simple = 'inputs/inputs_simple_sf'
inputs_simple_total = 'inputs/inputs_simple_total'
inputs_params = 'inputs/inputs_params_sf'
inputs_params_wind = 'inputs/inputs_params_wind'
inputs_params_pv = 'inputs/inputs_params_pv'
inputs_params_csp = 'inputs/inputs_params_csp'

inputs_simple_onshore_wind =  inputs_simple+"Wind-onshore"
inputs_simple_offshore_wind =  inputs_simple+"Wind-offshore"
inputs_simple_pv = inputs_simple+"mono-Si-PV"
inputs_simple_csp = inputs_simple+"ST-salt-TES"

def main():
    print "Hello"
    
# Generic function for the inequality constraint x[1] + x[2] <= 1
def non_complementary_constraint(i, j):
    def g(x):
        return np.array([-x[i] - x[j] + 1])
    return g
def binary_bounds(n):
    bnds = []
    for i in range(0, n):
        bnds.append((0.0, 1.0))
    return bnds

def loadData(opti_inputs):
     data = genfromtxt(opti_inputs, delimiter='\t', dtype=None)
     lats = data[:, 0]; lon = data[:, 1]
     total_area = data[:, 2]
     # Potential suitable area for each technology
     area = data[:, 3:6]
     c = data[:, 6]; k = data[:, 7]; ghi = data[:, 8]; dni = data[:, 9]
     embodiedE1y_wind = data[:, 10]
     operationE_wind = data[:, 11]
     avail_wind = data[:, 12]
     keMax = data[:,13]
     return (lats, lon, total_area, area, c, k, ghi, dni, embodiedE1y_wind, operationE_wind, avail_wind, keMax)

def loadDataSimpleModel(opti_inputs):
     data = genfromtxt(opti_inputs, delimiter='\t', dtype=None)
     lats = data[:, 0]; lon = data[:, 1]
     total_area = data[:, 2]
     # Potential suitable area for each tecnology
     area = data[:, 3:6]
     eff = data[:, 6:9]
     ressources = data[:, 9:12]
     installed_capaciy_density = data[:, 12:15]
     embodiedE1y = data[:, 15:18]
     operationE = data[:, 18:21]
     keMax = data[:, 21]
     return (lats, lon, total_area, area, eff, ressources, installed_capaciy_density, embodiedE1y, operationE, keMax)
 
def loadDataSimpleModelOneTech(opti_inputs):
     data = genfromtxt(opti_inputs, delimiter='\t', dtype=None)
     lats = data[:, 0]; lon = data[:, 1]
     total_area = data[:, 2]
     # Potential suitable area for each tecnology
     area = data[:, 3]
     eff = data[:, 4]
     ressources = data[:, 5]
     installed_capaciy_density = data[:, 6]
     embodiedE1y = data[:, 7]
     operationE = data[:, 8]
     keMax = data[:, 9]
     return (lats, lon, total_area, area, eff, ressources, installed_capaciy_density, embodiedE1y, operationE, keMax)

def loadDataWind():
    data = genfromtxt(inputs_params_wind, delimiter='\t', dtype=None)
    # Lats, lons, area, suitable area, c, k, EE, OE, avail, keMax
    return (data[:, 0],data[:, 1],data[:, 2],data[:, 3],data[:, 4],data[:, 5],data[:, 6],data[:, 7],data[:, 8],data[:, 9])
def loadDataPV():
    data = genfromtxt(inputs_params_pv, delimiter='\t', dtype=None)
    # Lats, lons, area, suitable area, ghi
    return (data[:, 0],data[:, 1],data[:, 2],data[:, 3],data[:, 4])
def loadDataCSP():
    data = genfromtxt(inputs_params_csp, delimiter='\t', dtype=None)
    # Lats, lons, area, suitable area, dni
    return (data[:, 0],data[:, 1],data[:, 2],data[:, 3],data[:, 4])
         
# Fixed inputs !
efficiency_PV = 0.18622918619208484
installed_capacity_density_PV = 240
operationE_PV = 0.0097
operationE_CSP = 0.07300000000000001
embodiedE1y_PV = 180.00355555555558
embodiedE1y_CSP_fixed = 231.78966666666662
embodiedE1y_CSP_area = 109.73390740740737
defaultCSP_area = 13.533834586466165

# Net Energy = energy produced [MWh/an] - embodied energy in installed capacity
# x is the vector corresponding to the % of each cells covered by a given technology
def netEnergySimpleModel(x, area, eff, ressources, installed_capaciy_density, operationE, embodiedE1y): 
    return sum(production(x, area, eff, ressources, operationE) - embodiedEnergy(x, area, installed_capaciy_density, embodiedE1y))

def eroiSimpleModel(x, area, eff, ressources, installed_capaciy_density, operationE, embodiedE1y): 
    return sum(grossProduction(x, area, eff, ressources)) / (sum(operationE*grossProduction(x, area, eff, ressources)) + sum(embodiedEnergy(x, area, installed_capaciy_density, embodiedE1y)))

# Production in MWh
def production(x, area, eff, ressources, operationE):
    if len(area) == 1:
        one = 1
    else:
        one = np.ones(len(x))
    return x * area * eff * ressources * (365 * 24) * (one - operationE)

def grossProduction(x, area, eff, ressources):
    return x * area * eff * ressources * (365 * 24)

def embodiedEnergy(x, area, installed_capaciy_density, embodiedE1y): 
    return x * area * installed_capaciy_density * embodiedE1y 
# C = Y - Ie - If
# C = E/qF - deltaE KE - deltaF KF
# C = E/qF (1- deltaF epsilonF vF) - cost_MW * MW_installed * 1/LF
# Results in $
# qF in MWh / $
def consumptionSimple(qF, vF, deltaF, epsilonF, deltaE, cost_MW, x, area, eff, ressources, installed_capaciy_density, operationE, embodiedE1y): 
    return sum((1-epsilonF*deltaF*vF)/qF*production(x, area, eff, ressources, operationE)) - capitalStockCost(x, area, installed_capaciy_density, deltaE, cost_MW)

def capitalStockCost(x, area, installed_capaciy_density, deltaE, cost_MW):
    return sum(x*area*installed_capaciy_density*deltaE*cost_MW)
    
def netEnergyScalar(x, area, c, k, ghi, dni, embodiedE1y_wind, operationE_wind, avail_wind):
    return netEnergyWind(x[0], area[0], x[3], x[4], c, k, embodiedE1y_wind, operationE_wind, avail_wind) + netEnergyPV(x[1], area[1], ghi) + netEnergyCSP(x[2], area[2], dni, x[5])
# Net Energy = energy produced [MWh/an] - embodied energy in installed capacity
# x is the vector corresponding to the % of each cells covered by a given technology
def netEnergy(x, area, c, k, ghi, dni, embodiedE1y_wind, operationE_wind, avail_wind):
    total = 0
    for i in range(0, len(c)):
        total += netEnergyWind(x[i*6], area[i*3], x[i*6+3], x[i*6+4], c[i], k[i], embodiedE1y_wind[i], operationE_wind[i], avail_wind[i]) + netEnergyPV(x[i*6+1], area[i*3+1], ghi[i]) + netEnergyCSP(x[i*6+2], area[i*3+2], dni[i], x[i*6+5])
    return total
def eroiScalar(x, area, c, k, ghi, dni, embodiedE1y_wind, operationE_wind, avail_wind):
    return (grossEnergyWind(x[0],area[0], x[3], x[4], c, k, avail_wind)+grossEnergyPV(x[1], area[1], ghi)+grossEnergyCSP(x[2], area[2], dni, x[5]))/(grossEnergyWind(x[0],area[0], x[3], x[4], c, k, avail_wind)*operationE_wind + grossEnergyPV(x[1], area[1], ghi)*operationE_PV + grossEnergyCSP(x[2], area[2], dni, x[5]) * operationE_CSP + embodiedEnergyWind(x[0], area[0], x[3], x[4], embodiedE1y_wind) + embodiedEnergyPV(x[1], area[1]) + embodiedEnergyCSP(x[2], area[2], x[4]))

def eroi(x, area, c, k, ghi, dni, embodiedE1y_wind, operationE_wind, avail_wind):
    grossWind = 0; grossPV = 0; grossCSP = 0; 
    oeWind = 0;
    eeWind = 0; eePV = 0; eeCSP = 0;
    for i in range(0, len(c)):
        gWind =  grossEnergyWind(x[i*6], area[i*3],  x[i*6+3], x[i*6+4], c[i], k[i], avail_wind[i])
        grossWind += gWind
        oeWind += gWind*operationE_wind[i]
        eeWind += embodiedEnergyWind(x[i*6], area[i*3],  x[i*6+3], x[i*6+4], embodiedE1y_wind[i])
        grossPV += grossEnergyPV(x[i*6+1], area[i*3+1], ghi[i])
        eePV += embodiedEnergyPV(x[i*6+1],area[i*3+1])
        grossCSP += grossEnergyCSP(x[i*6+2], area[i*3+2], dni[i], x[i*6+5])
        eeCSP += embodiedEnergyCSP(x[i*6+2], area[i*3+2], x[i*6+5])
    
    return (grossWind + grossPV + grossCSP)/(oeWind + grossPV*operationE_PV + grossCSP*operationE_CSP + eeWind + eePV + eeCSP)
    
def netEnergyIndexes(x, indWind, indPV, indCSP, area, c, k, ghi, dni, embodiedE1y_wind, operationE_wind, avail_wind):
    total = 0
    for i in indW:
        total += netEnergyWind(x[i[1]], area[i[0]], x[i*6+3], x[i*6+4], c[i], k[i], embodiedE1y_wind[i], operationE_wind[i], avail_wind[i]) 
    for i in range(0, len(c)):
        total += netEnergyWind(x[i*6], area[i*3], x[i*6+3], x[i*6+4], c[i], k[i], embodiedE1y_wind[i], operationE_wind[i], avail_wind[i]) + netEnergyPV(x[i*6+1], area[i*3+1], ghi[i]) + netEnergyCSP(x[i*6+2], area[i*3+2], dni[i], x[i*6+5])
    return total

def grossEnergyWind(x, area, vr, n, c, k, avail_wind):
    return x * area * installedCapacityDensityWind(vr, n) * capacityFactor(c, k, vr) * arrayEfficiency(n) * avail_wind * (365 * 24)
def energyWind(x, area, vr, n, c, k, operationE_wind, avail_wind):
    return grossEnergyWind(x, area, vr, n, c, k, avail_wind) * (1 - operationE_wind)
def embodiedEnergyWind(x, area, vr, n, embodiedE1y_wind):
    return x * area * installedCapacityDensityWind(vr, n) * embodiedE1y_wind
def netEnergyWind(x, area, vr, n, c, k, embodiedE1y_wind, operationE_wind, avail_wind):
    return energyWind(x, area, vr, n, c, k, operationE_wind, avail_wind) - embodiedEnergyWind(x, area, vr, n, embodiedE1y_wind)
def netEnergyWindOnly(x, area, c, k, embodiedE1y_wind, operationE_wind, avail_wind):
    total = 0
    for i in range(0, len(c)):
        total += netEnergyWind(x[i*3], area[i], x[i*3+1], x[i*3+2], c[i], k[i], embodiedE1y_wind[i], operationE_wind[i], avail_wind[i]) 
    return total

def grossEnergyPV(x, area, ghi):
    return x * area * efficiency_PV * ghi * (365 * 24)                                                     
def embodiedEnergyPV(x,area):
    return x * area * installed_capacity_density_PV * embodiedE1y_PV
def netEnergyPV(x, area, ghi):
    return grossEnergyPV(x,area,ghi) * (1 - operationE_PV) - embodiedEnergyPV(x, area) 
def netEnergyPVOnly(x, area, ghi):
    total = 0
    for i in range(0, len(ghi)):
        total += grossEnergyPV(x[i],area[i],ghi[i]) * (1 - operationE_PV) - embodiedEnergyPV(x[i], area[i]) 
    return total

def grossEnergyCSP(x, area, dni, sm):
    return x * area * efficiencyCSP(dni, sm) * dni * (365 * 24)
def netEnergyCSP(x, area, dni, sm):
    return grossEnergyCSP(x, area, dni, sm) * (1 - operationE_CSP) - embodiedEnergyCSP(x, area, sm)
def embodiedEnergyCSP(x, area, sm):
    return embodiedE1y_CSP_fixed * ratedPowerCSP(sm, x * area) + embodiedE1y_CSP_area * x * area / defaultCSP_area
def netEnergyCSPOnly(x, area, dni):
    total = 0
    for i in range(0, len(dni)):
        total += netEnergyCSP(x[i*2],area[i],dni[i],x[i*2+1])
    return total
# WIND
def capacityFactor(c, k, vr):
    vf = 25.0; vc = 3.0;
    return -math.exp(-math.pow(vf / c, k)) + (3 * math.pow(c, 3) * math.gamma(3.0 / k) / (k * (math.pow(vr, 3) - math.pow(vc, 3)))) * (gammainc(3.0 / k, math.pow(vr / c, k)) - gammainc(3.0 / k, math.pow(vc / c, k)))
def arrayEfficiency(n):
    a = 0.9838; b = 42.5681;
    return a * math.exp(-b * math.pi / (4 * n * n))
# W/m2
def installedCapacityDensityWind(vr, n, airDensity=1.225, cp=0.5):
    if n == 0: return 0
    else: return (0.5 * cp * airDensity * math.pi / 4.0 * math.pow(vr, 3)) / math.pow(n, 2)

# SOLAR
def lifeTimeEfficiency(eff, pr, degradationRate, lifetime):
    if degradationRate == 0: return eff * pr
    else: return  eff * pr * ((1.0 - math.pow(1.0 - degradationRate, lifetime)) / degradationRate) / lifetime
# CSP
def efficiencyCSP(dni, sm):
    def a(sm):
        return -1.578 * sm + 11.17
    def b(sm):
        return 10.65 * sm - 66.33
    if dni == 0: return 0
    else: return max(lifeTimeEfficiency((a(sm) * math.log(dni * 8.76) + b(sm)) / 100.0, 1.0, 0.2 / 100, 30),0)
    
def ratedPowerCSP(sm, area):
    return area * 950 * 0.22 / sm

# Only take the indexes where there is a potential (area > 0) for the optimization problem
# Then regirster the indexes where we should add a complementary constraint
def getIndexesSimpleModel(area):
    indexes = []; indexes_cons = []; k = 0; indexes_wind = []
    for i in range(0, len(area) / 3):
        for j in range(0, 3):
            index = i * 3 + j
            if area[i * 3 + j] > 0:
                indexes.append(index)
                if j == 0:
                    indexes_wind.append([k,index])
                if j == 2 and indexes[len(indexes)-2] == index - 1:
                    indexes_cons.append([k - 1, k])
                k += 1
    return (np.array(indexes), np.array(indexes_cons),  np.array(indexes_wind))

def getIndexesConsumptionModel(area, operationE, deltaE, epsilonE):
    indexes = []; indexes_cons = []; k = 0; indexes_wind = [];
    deltaE_indexes = []; epsilonE_indexes = [];
    for i in range(0, len(area) / 3):
        for j in range(0, 3):
            index = i * 3 + j
            if area[i * 3 + j] > 0:
                # Wind onshore
                if j == 0 and operationE[index] == 0.035:
                    deltaE_indexes.append(deltaE[j]); epsilonE_indexes.append(epsilonE[j]);
                else:
                    deltaE_indexes.append(deltaE[j+1]); epsilonE_indexes.append(epsilonE[j+1]);
                indexes.append(index)
                if j == 0:
                    indexes_wind.append([k,index])
                if j == 2 and indexes[len(indexes)-2] == index - 1:
                    indexes_cons.append([k - 1, k])
                k += 1
    return (np.array(indexes), np.array(indexes_cons),  np.array(indexes_wind) ,np.array(deltaE_indexes), np.array(epsilonE_indexes))

def getIndexes(area):
    ind_x = []; 
    ind_wind = []; ind_csp = []; ind_cons = []; k = 0;
    for i in range(0, len(area) / 3):
        for j in range(0, 3):
            index = i * 3 + j
            if area[i * 3 + j] > 0:
                ind_x.append(index)
                if j == 0: ind_wind.append([k,index])
                if j == 2: ind_csp.append([k,index])
                if j == 2 and ind_x[len(indexes)-2] == index - 1:
                    ind_cons.append([k - 1, k])
                k += 1
    return (np.array(ind_x), np.array(ind_cons), np.array(ind_wind), np.array(ind_csp))

# Results grid with 3 decision variable per cell (x_wind, x_pv, x_csp)
def writeResultsGrid(output_file, start, n, lats, lon, res, nX=3):
    output = open(output_file, 'w')
    for i in range(0, n):
       output.write(str(lats[i+start]) + "\t" + str(lon[i+start]) + "\t")
       resIndex = i * nX; x = np.zeros(nX);
       for j in range(0, nX):
           x[j] = res[1][resIndex + j]
           output.write(str(x[j]) + "\t")
       output.write("\n")
    output.close()
    return

# Results grid with 3 decision variable per cell (x_wind, x_pv, x_csp)
def writeDetailedResultsGrid(output_file, start, n, lats, lon, res, area, total_area,  c, k, nX=3):
    output = open(output_file, 'w')
    for i in range(0, n):
       output.write(str(lats[i+start]) + "\t" + str(lon[i+start]) + "\t")
       resIndex = i * nX; x = np.zeros(nX);
       for j in range(0, nX):
           x[j] = res[1][resIndex + j]
           output.write(str(x[j]) + "\t")
           if j<3:
               area_x = area[i+start,j]*x[j]
               output.write(str(area_x) + "\t")
               if total_area[i+start] > 0: output.write(str(area_x/total_area[i+start]) +"\t")
               else: output.write("0.0" +"\t")
       if(nX == 6):
           output.write(str(capacityFactor(c[i+start], k[i+start], x[3]))  +'\t')
       output.write("\n")
    output.close()
    return

def writeResultsCell(output, lat, lon, res):
    output.write(str(lat) + "\t" + str(lon) + "\t")
    output.write(str(res[0]))
    for i in range(0, len(res[1])):
        output.write("\t" + str(res[1][i]))
    output.write("\n")
    return

def writeDetailedResultsCell(output, lat, lon, res, area, total_area):
    output.write(str(lat) + "\t" + str(lon) + "\t")
    output.write(str(res[0])) # / 1000))
    for i in range(0, len(res[1])):
        output.write("\t" + str(res[1][i]))
        if i<3:
            output.write("\t" + str(res[1][i]*area[i]))
            output.write("\t" + str((res[1][i]*area[i])/total_area))
        
    output.write("\n")
    return
if __name__ == "__main__":
    sys.exit(main())